from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
from rich import print

from money import Money, Currency
from utilities import add_to_dict, get_currency_string
from constants import *

STOCK_TRANSACTION_CODES = [
    "QZ", "QA",     # Buy/Sell       (Al/Sat)
    "HX", "HF",                 # Public Offer           (Halka Arz)
    "RP", "RS", "RC"            # Capitalization Issue   (Pay Arttırımız)
]
STOCK_OTHER_CODES = [
    "RZ", "ZG"                     # Payouts                (Temettü)
]
STOCK_TRANSFER = "FV"           # Stock Transfer (Kıymet Virmanı)

SELL_STOCK_CODE = "QZ"
BUY_STOCK_CODE = "QA"
BUY_STOCK_CODE_SECONDARY = "ZG"
PUBLIC_OFFER_CODE = "HX"

class Stock:
    def __init__(self, code: str):
        self.count = 0
        self.net_money_spent = Money(0, Currency.TRY)
        self.code = code

        self.name = None
        self.price = None
        self.ticker = None

    def get_est_profit(self, cur: Currency=None) -> float:
        if cur is None:
            cur = self.net_money_spent.currency

        return self.get_est_sell_val(cur) + self.net_money_spent.get_val(cur)

    def get_name(self) -> str:
        if self.name is not None:
            return self.name
        
        info = self.get_ticker().info
        self.name = info["longName"] if "longName" in info.keys() else info["shortName"]
        return self.name

    def get_est_sell_val(self, cur: Currency=None) -> float:
        if cur is None:
            cur = self.net_money_spent.currency
        
        if self.price is None:
            ticker = self.get_ticker()
            self.price = Money(ticker.history(period="1d")['Close'][-1], Currency.from_str(ticker.info["currency"]))

        return (self.count * self.price).get_val(cur)
    
    def get_price_at(self, date: datetime, date_range:int=10) -> Money:
        ticker = self.get_ticker()
        history = ticker.history(start=(date - timedelta(days=date_range)).strftime("%Y-%m-%d"), end=(date + timedelta(days=1)).strftime("%Y-%m-%d"))
        if not history.empty:
            # Get the closing price for the date
            closing_price = history.iloc[0]["Close"]
            return Money(closing_price, Currency.from_str(ticker.info["currency"]))
        else:
            raise ValueError(f"No price data available for {date.strftime('%Y-%m-%d')}")

    def get_ticker(self) -> yf.Ticker:
        if self.ticker is not None:
            return self.ticker
        
        self.ticker = yf.Ticker(f"{self.code}.IS")
        return self.ticker

    def __repr__(self):
        return f"{self.code}: {self.net_money_spent}, {self.count} {self.price}"

def get_stocks(history: pd.DataFrame, excluded_stock_codes: list[str]) -> float:
    stocks = {}
    for i in reversed(range(len(history))):
        row = history.iloc[i]

        is_transaction = row[OP_TYPE_COL] in STOCK_TRANSACTION_CODES
        is_tax = row[OP_TYPE_COL] in STOCK_OTHER_CODES

        # Skip unrelated rows
        if not (is_transaction or is_tax or row[OP_TYPE_COL] == STOCK_TRANSFER):
            continue

        # Extract the stock code.
        desc = row[DESC_COL]
        stock_code = desc.split("-")[0].strip()

        # Skip excluded funds
        if stock_code in excluded_stock_codes:
            continue

        if stock_code == "ALTIN":
            print("[bold red][UYARI][/bold red] [yellow]Altın Darphane Sertifikası (ALTIN.S1)[/yellow] desteklenmediğinden dolayı atlanacaktır.")
            continue

        # Create a new fund if it does not exist.
        if stock_code not in stocks.keys():
            stocks[stock_code] = Stock(stock_code)

        cost = Money(row[COST_COL], Currency.TRY, datetime.strptime(row[DATETIME_COL], r"%d/%m/%Y-%H:%M:%S"))

        count = 0
        try:
            count = round(float(desc.split(" ")[-1].replace(",", "")))
        except ValueError:
            pass

        if row[OP_TYPE_COL] == STOCK_TRANSFER:
            print(f"[bold yellow][BİLGİLENDİRME][/bold yellow] {stock_code} seneti için {count} adet kıymet virmanı tespit edildi. Virmanın tam fiyat üzerinden yapıldığı varsayılıyor.")
            stocks[stock_code].count += count
            stocks[stock_code].net_money_spent += count * stocks[stock_code].get_price_at(datetime.strptime(row[DATETIME_COL], r"%d/%m/%Y-%H:%M:%S"))
            continue

        if is_transaction:
            stocks[stock_code].count += count
        stocks[stock_code].net_money_spent += cost

    return list(stocks.values())
   