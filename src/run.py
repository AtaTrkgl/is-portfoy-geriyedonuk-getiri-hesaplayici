from os import listdir
import pandas as pd
import warnings
from datetime import datetime
from rich import print
from rich.console import Console

from fund import calculate_fund_profit
from other_commisions import calculate_other_commisions
from stock import calculate_stock_profit
from utilities import get_currency_string

FILENAME_HINT = "HesapOzeti"
DATE_FORMAT = "%d-%m-%Y"

if __name__ == "__main__":
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
    file_names = listdir()

    # Find the file names
    account_file_name = ""
    for file_name in file_names:
        if FILENAME_HINT in file_name and account_file_name == "":
            account_file_name = file_name
            break

    if account_file_name == "":
        assert "Account file couldn't be found"

    start_date_str = input("Please Enter a start date (DD-MM-YYYY): ")
    start_date = datetime.strptime(start_date_str, DATE_FORMAT) if start_date_str != "" else datetime(1990, 1, 1)
    
    excluded_stocks = input("Enter stock names you want to excluded, seperated by comma: ").upper().split(",")
    excluded_funds = input("Enter fund codes you want to excluded, seperated by comma: ").split(",")

    console = Console()
    console.clear()

    print(f"[italic white]Calculating profits since {start_date.strftime(DATE_FORMAT)}" + (
        f", [italic white]excluding stocks: {excluded_stocks}" if excluded_stocks != [""] else "") + (
        f", [italic white]excluding funds: {excluded_funds}" if excluded_funds != [""] else ""))

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

    # Clear previous data
    for i, row in enumerate(account_history.iloc):
        date = datetime.strptime(row["İşlem Tarihi"].split("-")[0].strip(), "%d/%m/%Y")
        if date < start_date:
            account_history = account_history.iloc[:i]
            break

    # Calculate the profits
    print("[bold cyan]" + "\n" + "=" * 20 + " FUNDS " + "=" * 20)
    fund_profit = calculate_fund_profit(account_history, excluded_funds)

    print("[bold cyan]" + "\n" + "=" * 20 + " STOCKS " + "=" * 20)
    stock_profit, stock_commisions = calculate_stock_profit(account_history, excluded_stocks)

    taxes, keeping = calculate_other_commisions(account_history)

    print(f"""

[bold cyan]==================== PROFIT ====================[/bold cyan]
Calculated Fund Profit:           {get_currency_string(fund_profit)}
Calculated Stock Profit:          {get_currency_string(stock_profit + stock_commisions)}

[bold cyan]=================== EXPANSES ===================[/bold cyan]
Calculated Stock Commisions:      {get_currency_string(-stock_commisions)}
Calculated Taxes Commisions:      {get_currency_string(taxes)}
Calculated Keeping Commisions:    {get_currency_string(keeping)}

[bold cyan]------------------------------------------------[/bold cyan]
Calculated Net Profit:            {get_currency_string(fund_profit + stock_profit + keeping + taxes)}
[italic]
Note: "Cached Out Profit" means the account holds
none of the following asset, and all of it has been
cached out. "Potential Profit" means the account still
holds some of the following asset, and the value is
cached out value plus the current worth of the assets
in hand (commision are not calculated for assets in hand).
""")
