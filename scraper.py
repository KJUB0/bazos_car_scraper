import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import sqlite3

base_url = "https://www.bazos.sk"
target_url = "https://www.bazos.sk/search.php?hledat=honda+civic+1.8+vtec&rubriky=www&hlokalita=&humkreis=25&cenaod=&cenado=&Submit=H%C4%BEada%C5%A5&order=&kitx=ano"

# file in which we save the extracted data
export_file_name = 'Honda_civic_1.8_vtec.csv'

# identities for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
} 

def site_download(url):
    print("Stahujem zdrojovy kod stranky.")

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        #print("Problem pri naciavani stranky.")
        return None
    else:
        return BeautifulSoup(response.text, "html.parser")
    
# finds offer card
def find_offers(soup):
    cards = soup.find_all("div", {"class" : "inzeraty inzeratyflex"})
    return cards

def extract_information(cards):
    data = []
    for card in cards:
        # find the h2 with class 'nadpis', then get the 'a' tag inside
        title_element = card.find('h2', class_='nadpis')
        
        # check if element exists to avoid crashes
        if title_element and title_element.find('a'):
            title = title_element.find('a').text.strip()
            link = title_element.find('a')['href']
        else:
            link = None
            title = None

        # extract price
        price_element = card.find('div', class_='inzeratycena')
        raw_price = price_element.text.strip()

        # extract location
        location_element = card.find('div', class_='inzeratylok')
        location = location_element.text.strip() if location_element else None

        # filtering logic
        is_car_valid = True

        if raw_price:
            clean_price = raw_price.replace("€", "").replace(" ", "")
            if clean_price.isnumeric():
                price_number = int(clean_price)

                # basic filter for car parts and wrecks
                if price_number < 500:
                    is_car_valid = False

            # try to keep all the non numeric price values("dohodou", "ponuknite")
            else:
                pass

        # store the pair
        if title and link and is_car_valid:
            data.append({
                'name': title,
                'price': raw_price,
                'location': location,
                'link' : link
            })

    return data

def save_to_db(dictionary_of_offers):

    if not dictionary_of_offers:
        print("Nemam co zapisat.")
        return
    
    # turning dictionary into pandas dataframe
    new_df = pd.DataFrame(dictionary_of_offers)
    db_name = 'bazos_cars.db' 

    # connect to database
    # if its non-existant we create it
    connection = sqlite3.connect(db_name)

    try:
        # load links from database
        existing_links = pd.read_sql("SELECT link FROM cars", connection)
        
        # filter by link
        only_new_cars = new_df[~new_df['link'].isin(existing_links['link'])]

    except pd.errors.DatabaseError:
        # case for clean save file (first run)
        print("Tabulka v databaze este neexistuje, vytvaram novu...")
        only_new_cars = new_df

    except Exception as e:
        print(f"Ina chyba pri citani databazy: {e}")
        only_new_cars = pd.DataFrame() # Empty dataframe to prevent crash

    if not only_new_cars.empty:
        print(f"Zapisujem {len(only_new_cars)} novych aut do SQL databazy.")
        
        # appends new data
        only_new_cars.to_sql('cars', connection, if_exists='append', index=False)
    else:
        print("Ziadne nove inzeraty (vsetky uz su v databaze).")
    connection.close()

def main():
    # number of elements for every page
    offset = 0 

    while True:

        # Url for looking through multiple pages 
        current_url = f"{target_url}&crz={offset}"

        # save the site
        soup = site_download(current_url)
    
        # chek if we've saved the site
        if soup == None:
            print("Stranku sa nepodarilo nacitat.")
            return
    
        # extract just the offer cards hrom html
        cards = find_offers(soup)

        # exit clause for when we have no more cards == end 
        if not cards:
            break

        print(f"Nasiel som {len(cards)} inzeratov na tejto strane")

        # extract for us important information from the cards
        offers = extract_information(cards)

        # we save the information into a file
        save_to_db(offers)

        offset+=20
        time.sleep(1)



if __name__ == "__main__":
    main()