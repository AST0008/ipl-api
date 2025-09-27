# import time
# import json
# import requests
# from bs4 import BeautifulSoup
# BASE_URL = "https://www.espncricinfo.com"
# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                   "AppleWebKit/537.36 (KHTML, like Gecko) "
#                   "Chrome/120.0.0.0 Safari/537.36",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Referer": "https://www.google.com/"
# }

# def get_match_links(season_url):
#     res = requests.get(season_url, headers=headers)
#     print(res.status_code)
#     print(res.text[:500])  # preview page HTML
#     soup = BeautifulSoup(res.text, "html.parser")
    
#     links = []
#     for a in soup.select("a[href*='full-scorecard']"):
#         links.append(BASE_URL+a["href"])
#     return links
        
    

# def prepare_scoreboard(link):
#     res = requests.get(link, headers=headers)
#     soup = BeautifulSoup(res.text, "html.parser")
    
#     match_data = {}
#     info = soup.select("div.ds-grow > span")
#     if info:
#         match_data["info"] = [span.get_text(" ", strip=True) for span in info]
#     print("info" , info)

#         # Teams
#     teams = [t.get_text(strip=True) for t in soup.select("span.ds-text-title-xs.ds-font-bold")]
#     match_data["teams"] = teams
#     print("teams", teams)

#     # Innings
#     match_data["innings"] = []
#     innings_divs = soup.select("div.ds-rounded-lg.ds-mt-2")

#     for inn in innings_divs:
#         inn_name = inn.select_one("span.ds-text-title-xs").text
#         table = inn.select_one("table")
#         rows = table.find_all("tr")

#         batting = []
#         for row in rows[1:]:
#             cols = row.find_all("td")
#             if len(cols) > 1:  # valid row
#                 batting.append({
#                     "player": cols[0].get_text(strip=True),
#                     "runs": cols[2].get_text(strip=True),
#                     "balls": cols[3].get_text(strip=True),
#                     "fours": cols[5].get_text(strip=True),
#                     "sixes": cols[6].get_text(strip=True),
#                     "strike_rate": cols[7].get_text(strip=True),
#                 })

#         match_data["innings"].append({"name": inn_name, "batting": batting})

#     return match_data
    

# if __name__ == "__main__":
#     season_url = "https://www.espncricinfo.com/series/ipl-2025-1449924/match-schedule-fixtures-and-results"
#     match_links = get_match_links(season_url)
#     print(f"Found {len(match_links) } matches ")
    
#     all_matches = []
    
#     for link in all_matches:
#         print("Scraping: ", link)
#         data = prepare_scoreboard(link)
#         all_matches.append(data)
#         time.sleep(2)
        
#     with open("ipl_2025.json", "w") as f:
#         json.dump(all_matches, f ,indent=2)


import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

BASE_URL = "https://www.espncricinfo.com"

def get_driver():
    """Initialize Chrome driver in headless mode"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # run without opening browser window
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_match_links(driver, season_url):
    """Scrape all match URLs from a season fixtures page"""
    driver.get(season_url)
    time.sleep(3)  # wait for JS to load

    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = []

    for a in soup.select("a[href*='full-scorecard']"):
        links.append(BASE_URL + a["href"])
    return links

def parse_scorecard(driver, url):
    """Scrape a single match scorecard"""
    driver.get(url)
    time.sleep(3)  # wait for page to load
    soup = BeautifulSoup(driver.page_source, "html.parser")

    match_data = {}

    # Match Info
    info_divs = soup.select("div.ds-grow > span")
    if info_divs:
        match_data["info"] = [span.get_text(" ", strip=True) for span in info_divs]

    # Teams
    teams = [t.get_text(strip=True) for t in soup.select("span.ds-text-tight-l")]
    match_data["teams"] = teams

    # Innings
    match_data["innings"] = []
    innings_divs = soup.select("div.ds-rounded-lg")
    # print("inngs_div",innings_divs )

    match_data["innings"] = []

    for inn in innings_divs:
        inn_name = inn.select_one("span.ds-text-title-xs").text
        table = inn.select_one("table")
        rows = table.find_all("tr")
        batting = []

        for row in rows[1:]:
            cols = row.find_all("td")

            # Only parse rows that look like actual batting rows (at least 8 columns)
            if len(cols) >= 8:
                try:
                    batting.append({
                        "player": cols[0].get_text(strip=True),
                        "runs": cols[2].get_text(strip=True),
                        "balls": cols[3].get_text(strip=True),
                        "fours": cols[5].get_text(strip=True),
                        "sixes": cols[6].get_text(strip=True),
                        "strike_rate": cols[7].get_text(strip=True),
                    })
                except IndexError:
                    continue  # skip malformed rows

    
            elif "Extras" in row.get_text():
                batting.append({"Extras": row.get_text(strip=True)})

        # Append the entire innings after processing all rows
        match_data["innings"].append({"name": inn_name, "batting": batting})

    # Return after processing all innings
    return match_data


if __name__ == "__main__":
    # Cricinfo IPL series URLs (2008–2024)
    seasons = {
        2008: "https://www.espncricinfo.com/series/ipl-2008-313494/match-schedule-fixtures-and-results",
        2009: "https://www.espncricinfo.com/series/ipl-2009-374163/match-schedule-fixtures-and-results",
        2010: "https://www.espncricinfo.com/series/ipl-2010-418064/match-schedule-fixtures-and-results",
        2011: "https://www.espncricinfo.com/series/ipl-2011-466304/match-schedule-fixtures-and-results",
        2012: "https://www.espncricinfo.com/series/ipl-2012-520932/match-schedule-fixtures-and-results",
        2013: "https://www.espncricinfo.com/series/ipl-2013-586733/match-schedule-fixtures-and-results",
        2014: "https://www.espncricinfo.com/series/ipl-2014-695871/match-schedule-fixtures-and-results",
        2015: "https://www.espncricinfo.com/series/ipl-2015-791129/match-schedule-fixtures-and-results",
        2016: "https://www.espncricinfo.com/series/ipl-2016-968923/match-schedule-fixtures-and-results",
        2017: "https://www.espncricinfo.com/series/ipl-2017-1078425/match-schedule-fixtures-and-results",
        2018: "https://www.espncricinfo.com/series/ipl-2018-1131611/match-schedule-fixtures-and-results",
        2019: "https://www.espncricinfo.com/series/ipl-2019-1165643/match-schedule-fixtures-and-results",
        2020: "https://www.espncricinfo.com/series/ipl-2020-21-1210595/match-schedule-fixtures-and-results",
        2021: "https://www.espncricinfo.com/series/ipl-2021-1249214/match-schedule-fixtures-and-results",
        2022: "https://www.espncricinfo.com/series/ipl-2022-1298423/match-schedule-fixtures-and-results",
        2023: "https://www.espncricinfo.com/series/ipl-2023-1345038/match-schedule-fixtures-and-results",
        2024: "https://www.espncricinfo.com/series/ipl-2024-1410320/match-schedule-fixtures-and-results",
    }

    driver = get_driver()

    for year, url in seasons.items():
        print(f"\n====== Scraping IPL {year} ======")
        match_links = get_match_links(driver, url)
        print(f"Found {len(match_links)} matches")

        all_matches = []
        for link in match_links:
            print("Scraping:", link)
            data = parse_scorecard(driver, link)
            all_matches.append(data)
            time.sleep(1)  # be nice to Cricinfo

        # Save season to JSON
        with open(f"ipl_{year}.json", "w", encoding="utf-8") as f:
            json.dump(all_matches, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved ipl_{year}.json")

    driver.quit()
