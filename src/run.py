from os import listdir
import pandas as pd
import warnings

from fund import calculate_fund_profit
from other_commisions import calculate_other_commisions
from stock import calculate_stock_profit

FUND_FILENAME_HINT = "Fon"
STOCK_FILENAME_HINT = "İşlem"
FILENAME_HINT = "HesapOzeti"

if __name__ == "__main__":
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
    file_names = listdir()

    # Find the file names
    fund_file_name = ""
    stock_file_name = ""
    account_file_name = ""
    for file_name in file_names:
        if FUND_FILENAME_HINT in file_name and fund_file_name == "":
            fund_file_name = file_name
        if STOCK_FILENAME_HINT in file_name and stock_file_name == "":
            stock_file_name = file_name
        if FILENAME_HINT in file_name and account_file_name == "":
            account_file_name = file_name

    if account_file_name == "":
        assert "Account file couldn't be found"

    # === Read the account history file ===

    # Remove the info texts
    account_history = pd.read_excel(account_file_name).iloc[14:]

    # Update headers
    account_history.reset_index(inplace=True, drop=True)
    headers = account_history.iloc[0]
    account_history = account_history.iloc[1:]

    # Clear the info texts
    account_history = account_history.iloc[:-7]
    account_history.columns = headers

    # Calculate the profits
    print("\n" + "=" * 20 + " FUNDS " + "=" * 20)
    fund_profit = calculate_fund_profit(account_history)

    print("\n" + "=" * 20 + " STOCKS " + "=" * 20)
    stock_profit, stock_commisions = calculate_stock_profit(account_history)

    taxes, keeping = calculate_other_commisions(account_history)

    print(f"""


==================== PROFIT ====================
Calculated Fund Profit:           {fund_profit:.2f}₺
Calculated Stock Profit:          {stock_profit + stock_commisions:.2f}₺

=================== EXPANSES= ==================
Calculated Net Stock Commisions: -{stock_commisions:.2f}₺
Calculated Taxes Commisions:      {taxes:.2f}₺
Calculated Keeping Commisions:    {keeping:.2f}₺

------------------------------------------------
Calculated Net Profit:            {fund_profit + stock_profit + keeping + taxes:.2f}₺
""")