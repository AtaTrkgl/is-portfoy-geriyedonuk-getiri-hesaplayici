from requests import get
from bs4 import BeautifulSoup
from fund_ids import FUND_ID_TO_CODE
from rich import print

from utilities import add_to_dict, currency_to_number, get_currency_string

FUND_CODES = ["MN", "73", "72"]
FUND_PRICES_URL = "https://www.isportfoy.com.tr/tr/yatirim-fonlari"

# Returns a dictionary of (fund label, fund price) where keys are fund codes.
def get_fund_data() -> dict:
    data_dict = {}
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

        data_dict[span.contents[0]] = (
            table_data[1].find("a").contents[0].replace("*", "").strip(),
            currency_to_number(table_data[4].find("a").contents[0]),
        )
    
    return data_dict

def get_fund_worth(fund_dict: dict, prices: dict) -> dict:
    worths = {}
    for key in fund_dict.keys():
        id = FUND_ID_TO_CODE[key]
        add_to_dict(worths, key, prices[id] * fund_dict[key])
    return worths


def calculate_fund_profit(df, excluded_funds) -> float:
    fund_dict = {}
    profits = {}
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
            
            add_to_dict(profits, fund, -price * amount)
            add_to_dict(fund_dict, fund, amount)

    # clear the funds that have been sold out.
    funds = list(fund_dict.keys())
    for fund in funds:
        if fund_dict[fund] == 0:
            fund_dict.pop(fund)

    fund_data = get_fund_data()
    current_worth = get_fund_worth(fund_dict, {k: v[1] for k, v in fund_data.items()})
    for fund in profits:
        fund_name = fund_data[FUND_ID_TO_CODE[fund]][0]
        if fund in current_worth.keys():
            print(f"[bold yellow]({fund}) {fund_name}:[/bold yellow] Potential Profit:  {get_currency_string(profits[fund] + current_worth[fund])}")
        else:
            print(f"[bold yellow]({fund}) {fund_name}:[/bold yellow] Cached Out Profit: {get_currency_string(profits[fund])}")

    return sum(list(profits.values())) + sum(list(current_worth.values()))