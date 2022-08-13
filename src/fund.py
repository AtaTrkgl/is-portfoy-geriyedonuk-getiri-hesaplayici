import pandas as pd
from requests import get
from bs4 import BeautifulSoup
from fund_ids import FUND_ID_TO_CODE

from utilities import add_to_dict, currency_to_number

FUND_CODES = ["MN", "73", "72"]
FUND_PRICES_URL = "https://www.isportfoy.com.tr/tr/yatirim-fonlari"

def get_fund_prices() -> dict:
    prices_dict = {}
    response = get(FUND_PRICES_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr")
    for row in rows:
        span = row.find("span")
        if span is None:
            continue

        table_data = row.find_all("td")
        if len(table_data) == 0:
            continue

        prices_dict[span.contents[0]] = currency_to_number(table_data[4].find("a").contents[0])
    
    return prices_dict

def get_fund_worth(fund_dict) -> float:
    if len(fund_dict) == 0:
        return 0

    prices_dict = get_fund_prices()
    
    balance = 0
    print("You still have funds that you haven't sold out yet.")
    print("Calculated the following worth from the funds you own:\n")
    for key in fund_dict.keys():
        id = FUND_ID_TO_CODE[key]
        print(f"{id} is now worth {prices_dict[id]} per fund, making a total of {prices_dict[id] * fund_dict[key]:.2f}₺")
        balance += prices_dict[id] * fund_dict[key]
    return balance


def calculate_fund_profit(df, excluded_funds) -> float:
    fund_dict = {}
    balance = 0
    for i in reversed(range(1, len(df["İşlem"]) + 1)):
        action_type = df["İşlem"][i]
        
        description = df["Açıklama"][i].replace(":+", ": +")
        fund = description.split("-")[0].strip()
        if fund in excluded_funds: continue
        splited_desc = description.split(" ")

        if action_type in FUND_CODES:
            amount = currency_to_number(splited_desc[-1], ".", ",")
            price = abs(currency_to_number(splited_desc[-3], ".", ","))
            if price <= 0:
                continue
            
            balance -= price * amount
            add_to_dict(fund_dict, fund, amount)

    # clear the funds that have been sold out.
    funds = list(fund_dict.keys())
    for fund in funds:
        if fund_dict[fund] == 0:
            fund_dict.pop(fund)

    return balance + get_fund_worth(fund_dict)