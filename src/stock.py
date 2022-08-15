import yfinance as yf
from rich import print

from utilities import add_to_dict, get_currency_string

SELL_STOCK_CODE = "QZ"
BUY_STOCK_CODE = "QA"
BUY_STOCK_CODE_SECONDARY = "ZG"
PUBLIC_OFFER_CODE = "HX"


def get_stocks_worth(stocks_dict: dict) -> dict:
    stocks = stocks_dict.keys() 

    current_values = {}
    for stock in stocks:
        stock_info = yf.Ticker(f"{stock}.IS").info
        price = stock_info["regularMarketPrice"]

        add_to_dict(current_values, stock, stocks_dict[stock] * price)
    
    return current_values


def calculate_stock_profit(df, excluded_stocks) -> float:
    stock_inventory = {}
    profits = {}
    total_commision = 0

    for i in reversed(range(1, len(df["İşlem"]) + 1)):
        action_type = df["İşlem"][i]
        
        description = df["Açıklama"][i]
        stock = description.split("-")[0].strip()
        if stock in excluded_stocks: continue
        splited_desc = description.split(" ")

        # Public offer order
        if action_type == PUBLIC_OFFER_CODE and "SENET GİRİŞİ" in description:
            amount = float(splited_desc[-1])
            price = float(splited_desc[-3])
            
            add_to_dict(profits, stock, -price * amount)
            add_to_dict(stock_inventory, stock, amount)

        # Buying a stock
        if action_type == BUY_STOCK_CODE:
            commision = abs(float(splited_desc[3])) + abs(float(splited_desc[6]))
            amount = abs(float(splited_desc[-1]))
            price = abs(float(splited_desc[-3]))

            total_commision += commision
            add_to_dict(profits, stock, -price * amount - commision)
            if price > 0:
                add_to_dict(stock_inventory, stock, amount)

        if action_type == BUY_STOCK_CODE_SECONDARY:
            amount = abs(float(splited_desc[-1]))
            price = abs(float(splited_desc[-3]))

            add_to_dict(profits, stock, -price * amount)
            add_to_dict(stock_inventory, stock, amount)

        # Selling a stock
        if action_type == SELL_STOCK_CODE:
            commision = abs(float(splited_desc[3])) + abs(float(splited_desc[6]))
            amount = abs(float(splited_desc[-1]))
            price = abs(float(splited_desc[-3]))

            total_commision += commision
            add_to_dict(profits, stock, price * amount - commision)
            add_to_dict(stock_inventory, stock, -amount)

    # clear the stocks that have been sold out.
    keys = list(stock_inventory.keys())
    for key in keys:
        if stock_inventory[key] == 0:
            stock_inventory.pop(key)

    
    current_worth = get_stocks_worth(stock_inventory)
    for stock in profits:
        if stock in current_worth.keys():
            print(f"[bold yellow]{stock}:[/bold yellow] Potential Profit:  {get_currency_string(profits[stock] + current_worth[stock])}")
        else:
            print(f"[bold yellow]{stock}:[/bold yellow] Cached Out Profit: {get_currency_string(profits[stock])}")

    return sum(list(profits.values())) + sum(list(current_worth.values())), total_commision
   