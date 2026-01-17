# bazos_car_scraper Bazos Car Scraper & Market Analyzer

Tento projekt je automatizovaný nástroj na zber dát z portálu Bazos.sk. Pôvodne bol spravený na sledovanie trhu s vozidlami Honda Civic 1.8 VTEC, ale vedel by som ho prisposobiť aj pre iné vozidlá pre hocijaké iné vyhľadávanie.

Cieľom projektu je nahradiť manuálne prezeranie inzerátov automatizovaným procesom, ktorý ukladá čisté dáta do SQL databázy pre ďalšiu analýzu. Pôvodne bolo v pláne dorobiť aj funkcionalitu pre discord bota, ktorý by posielal upozornenia na moj server, ale od toho som nakoniec upustil. 

Funkcionalita

    Web Scraping: Skript prechádza všetky stránky vyhľadávania pomocou knižnice BeautifulSoup a Requests.

    Čistenie dát:

        Extrakcia názvu, ceny, lokality a odkazu.

        Konverzia cien na numerické hodnoty.

        Filtrácia nerelevantných inzerátov (náhradné diely alebo vraky pod 500€).

    Ukladanie dát:

        Využitie Pandas na prácu s databázou.

        Dáta sú ukladané do SQLite databázy (.db súbor).

        Kontrola duplikácii: Skript pred zápisom kontroluje, či inzerát už v databáze existuje, aby sa predišlo duplicitám.

Použité jazyky + knižnice

    Python 

    Pandas (Manipulácia s dátami)

    SQLite (Databáza)

    BeautifulSoup4 (HTML Parsing)

    Requests (HTTP požiadavky)