from datetime import datetime

from requests import get
from bs4 import BeautifulSoup
from rich import print
import pandas as pd

from money import Money, Currency
from constants import *

FUND_TRANSACTION_CODES = ["72", "73", "MN"]
FUND_TAX_CODES = ["VG"]

FUND_PRICES_URL = "https://www.isportfoy.com.tr/getiri-ve-fiyatlar"
FUNDS_LIST_URL = "https://www.isbank.com.tr/tefas"

class Fund:
    fund_data_dict = None
    def __init__(self, code: str):
        self.count = 0
        self.net_money_spent = Money(0, Currency.TRY)
        self.code = code

    def get_name(self) -> str:
        return Fund.get_fund_data_dict()[self.code]["name"]

    def get_est_profit(self, cur: Currency=None) -> float:
        if cur is None:
            cur = self.net_money_spent.currency

        return self.get_est_sell_val().get_val(cur) + self.net_money_spent.get_val(cur)

    def get_est_sell_val(self) -> Money:
        fund_data = Fund.get_fund_data_dict()[self.code]
        return Money(self.count * fund_data["price"], fund_data["currency"], datetime.now())
    
    @staticmethod
    def get_fund_data_dict():
        if Fund.fund_data_dict is not None:
            return Fund.fund_data_dict
        
        print("Fetching fund data...")
        Fund.fund_data_dict = {}

        # If we don't mimic a browser like this, the website returns a "bot detected" page.
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # First, fetch the TEFAŞ Fund list.
        b = BeautifulSoup(get(FUNDS_LIST_URL, headers=headers).text, features="lxml")
        for tr in b.find("tbody").find_all("tr"):
            fund_trade_code = tr.find("th").text.strip()
            rest = [td.text.strip() for td in tr.find_all("td")]

            currency = Currency.from_str(rest[0])

            # rest: [Currency, Fund Code, Fund Name]
            Fund.fund_data_dict[rest[1]] = {
                "trade_code": fund_trade_code,
                "currency": currency,
                "name": rest[2]
            }

        # Then, add some funds that are not in the list, manually.
        # TODO: Find a way to fetch these funds automatically.
        funds_to_add_manually = {
            "804": "TI4",
            "807": "TI7",
            "835310": "IBB",
            "817": "TGE",
            "835408": "ITP",
            "835422": "IKL",
            "835434": "IKP",
            "835440": "IJP",
            "835446": "IJB",
            "835450": "IJZ",
            "835452": "IJC",
            "835311": "IPJ",
            "814": "TMG",
            "816": "TDG",
            "802": "TI2",
            "835397": "IDH",
            "835428": "IHK",
            "803": "TI3",
            "809": "TIE",
            "811": "TAU",
            "812": "TTE",
            "835556": "IPG",
            "835423": "ILZ",
            "835389": "KKH",
            "835456 ": "IJT",
            "835543": "IEV",
            "821": "TMC",
            "835428": "IHK",
            "835434": "IKP",
            "810": "TKK",
            "801": "TI1",
            "808": "TIV",
            "818": "TSI",
            "824": "IBK",
            "806": "TI6",
            "835291": "IPV",
            "813": "TBV",
            "822": "TTA",
            "835038": "IAT",
        }

        for code, trade_code in funds_to_add_manually.items():
            Fund.fund_data_dict[code] = {
                "trade_code": trade_code,
                "currency": Currency.TRY,
                "name": "?"
            }

        # Then, fetch the fund prices. While doing this, get the names of the manualy added funds.
        b = BeautifulSoup(get(FUND_PRICES_URL, headers=headers).text, features="lxml")
        for tr in b.find_all("tr"):
            td = tr.find("td")
            if td is None:
                continue
            
            sp = td.find("span")
            if sp is None:
                continue
            
            code = sp.text.strip()

            price = float(tr.find_all("td")[2]["data-value"].replace(".", "").replace(",", "."))
            for fund_code, fund_data in Fund.fund_data_dict.items():
                if fund_data["trade_code"] == code:
                    Fund.fund_data_dict[fund_code]["price"] = price
                    
                    # Update the name of the manually added funds.
                    if Fund.fund_data_dict[fund_code]["name"] == "?":
                        Fund.fund_data_dict[fund_code]["name"] =tr.find_all("td")[0]["data-value"]

        return Fund.fund_data_dict

def create_funds(history: pd.DataFrame, excluded_fund_codes: list[str]) -> float:
    funds = {}
    for i in reversed(range(len(history))):
        row = history.iloc[i]
        
        is_transaction = row[OP_TYPE_COL] in FUND_TRANSACTION_CODES
        is_tax = row[OP_TYPE_COL] in FUND_TAX_CODES

        # Skip unrelated rows
        if not (is_transaction or is_tax):
            continue

        # Extract the fund code.
        desc = row[DESC_COL]
        fund_code = desc.split("-")[0].strip()

        # Skip excluded funds
        if fund_code in excluded_fund_codes:
            continue

        # Create a new fund if it does not exist.
        if fund_code not in funds.keys():
            funds[fund_code] = Fund(fund_code)

        cost = Money(row[COST_COL], Currency.TRY, datetime.strptime(row[DATETIME_COL], r"%d/%m/%Y-%H:%M:%S"))
        count = 0

        if is_transaction:
            try:
                count = round(float(desc.split(" ")[-1].replace(",", "")))
            except ValueError:
                pass

        funds[fund_code].count += count
        funds[fund_code].net_money_spent += cost

    return list(funds.values())