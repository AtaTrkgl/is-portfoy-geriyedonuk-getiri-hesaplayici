import yfinance as yf

from utilities import currency_to_number, add_to_dict

SELL_STOCK_CODE = "QZ"
BUY_STOCK_CODE = "QA"
BUY_STOCK_CODE_SECONDARY = "ZG"
PUBLIC_OFFER_CODE = "HX"


def get_stock_prices(stocks_dict: dict) -> float:
    stocks = stocks_dict.keys() 
    if len(stocks) == 0:
        return 0

    balance = 0
    print("You still have stocks that you haven't sold out yet.")
    print("Calculated the following worth from the stocks you own:\n")
    for stock in stocks:
        stock_info = yf.Ticker(f"{stock}.IS").info
        price = stock_info["regularMarketPrice"]

        print(f"{stock} is now worth {price} per slot, making a total of {stocks_dict[stock] * price:.2f}₺")
        balance += stocks_dict[stock] * price
    
    return balance


def calculate_stock_profit(df) -> float:
    stock_inventory = {}
    profit = 0
    total_commision = 0

    for i in reversed(range(1, len(df["İşlem"]) + 1)):
        action_type = df["İşlem"][i]
        
        description = df["Açıklama"][i]
        stock = description.split("-")[0].strip()
        splited_desc = description.split(" ")

        # Public offer order
        if action_type == PUBLIC_OFFER_CODE and "SENET GİRİŞİ" in description:
            amount = float(splited_desc[-1])
            price = float(splited_desc[-3])
            
            profit -= price * amount
            add_to_dict(stock_inventory, stock, amount)

        # Buying a stock
        if action_type == BUY_STOCK_CODE:
            commision = abs(float(splited_desc[3])) + abs(float(splited_desc[6]))
            amount = abs(float(splited_desc[-1]))
            price = abs(float(splited_desc[-3]))

            total_commision += commision
            if price > 0:
                profit -= price * amount + commision
                add_to_dict(stock_inventory, stock, amount)
            else:
                profit -= commision

        if action_type == BUY_STOCK_CODE_SECONDARY:
            amount = abs(float(splited_desc[-1]))
            price = abs(float(splited_desc[-3]))

            profit -= price * amount
            add_to_dict(stock_inventory, stock, amount)

        # Selling a stock
        if action_type == SELL_STOCK_CODE:
            commision = abs(float(splited_desc[3])) + abs(float(splited_desc[6]))
            amount = abs(float(splited_desc[-1]))
            price = abs(float(splited_desc[-3]))

            profit += price * amount - commision
            total_commision += commision
            add_to_dict(stock_inventory, stock, -amount)

    # clear the stocks that have been sold out.
    keys = list(stock_inventory.keys())
    for key in keys:
        if stock_inventory[key] == 0:
            stock_inventory.pop(key)

    return profit + get_stock_prices(stock_inventory), total_commision
   