#Scraping the top 100 bestselling games on Steam.
from types import NoneType
import time
import requests
from bs4 import BeautifulSoup
from helium import *

steam_topsellers_url = 'https://store.steampowered.com/search/?supportedlang=english&filter=topsellers&ndl=1'
price = []
game_title = []
publish_date = []
links = []
developers = []
tags = []
publishers = []
variables = [price, game_title, publish_date, links]


def top_sellers():
    """

    """
    if requests.get(steam_topsellers_url).status_code == 200:
        while len(game_title) < 100 or len(links) < 100:
            driver = start_chrome(steam_topsellers_url, headless=True)
            for _ in range(1,10):
                scroll_down(num_pixels=100)
                scrape(driver)
            kill_browser()
        if len(game_title) < 100 or len(links) < 100:
            print(f"Retrying: Titles: {game_title}, Links: {links}")
            time.sleep(1)
    else:
        print("Connection error")

def scrape(driver):
    """
    Scrape any steam search page for Game Title and Link

    You must define a steam url and parser before calling scrape()

    *Note: Helium offers a simpler method of retrieving the html
    elements present on the driver's page with the S() selector,
    however, I wanted to showcase my familiarity with the beautiful
    soup package alongside navigating a dynamically loading webpage.
    """
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # Find links to each game
    link = soup.find_all('a', class_='search_result_row ds_collapse_flag')

    for tag in link[:102]:
        if tag.attrs["href"] not in links and len(links) < 100:
                links.append(tag.attrs["href"])
    #Get each variable from each game
    price_class = "discount_final_price"

    name_class = "title"
    for i in soup.find_all(class_=name_class):
        if i.text not in game_title and len(game_title) < 100:
            game_title.append(i.text)

#Scrape the dynamic Top 100 list
top_sellers()
print("title",game_title)
print(len(game_title))


#Navigate to each link and retrieve Publish Date, Developers and Publishers
def extract(el):
    return el.text.strip() if el else None
print(links)
print(len(links))

def list_append(variable, value):
    try:
        variable.append(value.text.strip())
    except TypeError or ValueError or NoneType:
        variable.append(None)

#Need to add helium code to select age from drop down

def select_age():
    day = S("@ageDay")
    select(day, "13")
    month = S("@ageMonth")
    select(month, "August")
    year = S("@ageYear")
    select(year, "2003")

def verify_age(driver):
    select_age()
    click('View Page')
    return driver.current_url

def get_variables(link):
    pages = requests.get(link)
    soup = BeautifulSoup(pages.content, 'html.parser')
    publish_date.append(extract(soup.find("div", class_="date")))
    developers.append(extract(soup.find("div", class_="summary column", id="developers_list")))
    publisher_div = soup.find("div", class_="subtitle column", string="Publisher:")

    if publisher_div:
        publisher = publisher_div.find_next_sibling("div", class_="summary column").a
        list_append(publishers, publisher)
    else:
        publishers.append(None)

    prices = soup.find("div", class_="game_purchase_price price")
    if not prices:
        prices = soup.find("div", class_="discount_final_price")
    if prices:
        list_append(price, prices)
    else:
        price.append(None)
def process_page(i):
    go_to(i)
    try:
        link = verify_age(driver)
        get_variables(link)
    except AttributeError:
        get_variables(i)


driver = start_chrome(headless=True)
for i in links:
    process_page(i)
kill_browser()
print("Developers:", developers)
print(len(developers))
print("Publishers:", publishers)
print(len(publishers))
print("Price:", price)
print(len(price))
print("Unformatted Dates:", publish_date)
print(len(publish_date))

from datetime import datetime

date_obj = []
days_published = []

def parse_dates(date):
    try:
        parsed_date = datetime.strptime(date, "%b %d, %Y")
        date_obj.append(parsed_date)

        delta = (date_today - parsed_date).days
        days_published.append(delta)
    except ValueError:
        print(f"Error in publish date for {game_title[index]} has format {date}")
        print("retrying format...")
        retry_format()

formats = ['%d,%m,%Y','%m,%Y']

def retry_format():
    for fmt in formats:
        try:
            date_obj.append(datetime.strptime(date, fmt))
        except ValueError:
            print("Could not format date")
            date_obj.append(None)

date_today = datetime.today()

def check_none(index, date):
    if date is None and game_title[index] == "Steam Deck":
        price[index] = 399.00
        return "Feb 25, 2022"
    elif date is None and game_title[index] == "Steam Deck Docking Station":
        price[index] = 79.00
        return "Oct 6, 2022"
    return date


for index, date in enumerate(publish_date):
    date = check_none(index, date)
    parse_dates(date)

print("Publish Dates:", publish_date)
print("# of Days Published:", days_published)
print(len(days_published))

#Since rankings are already ordered and retrieved in the order of highest to lowest, a simple list will do
rank = list(range(1,101))

#Create the Data Frame
import pandas as pd
Data = {'Title': game_title, 'Price': price, 'Rank': rank, 'Date Published': publish_date,'Days Published': days_published}
df = pd.DataFrame(Data)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
print(df)

#Create timestamp as data changes regularly
timestamp = datetime.now()
Data['timestamp'] = timestamp.isoformat()