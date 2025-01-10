from os import listdir
import pandas as pd
import warnings
from datetime import datetime
from rich import print

from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

import argparse
from money import Money, Currency

from fund import create_funds
from other_commisions import calculate_commisions
from stock import get_stocks
from utilities import get_currency_string
from constants import *

FILENAME_HINT = "HesapOzeti.xls"
DATE_FORMAT = "%d-%m-%Y"

# Argument parser
parser = argparse.ArgumentParser(prog="İŞ Portföy - Kazanç Hesaplayıcı", description="İŞ Bankası yatırım hesabı, hesap özetini kullanarak kazanç hesaplar.")

parser.add_argument(
    "-exclude_stocks", default="", type=str,
    help="Hesaba katılmayacak hisse senetlerini belirler. Virgülle ayrılmış hisse senedi isimleri girilmelidir."
)

parser.add_argument(
    "-exclude_funds", default="", type=str,
    help="Hesaba katılmayacak fonları belirler. Virgülle ayrılmış fon kodları girilmelidir."
)

if __name__ == "__main__":
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

    # === PARSE ARGUMENTS ===
    args = parser.parse_args()
    excluded_stocks = args.exclude_stocks.upper().split(",")
    excluded_funds = args.exclude_funds.split(",")

    console = Console()
    console.clear()

    # === PRINT INPUTS ===
    exclude_stocks_part = f", [italic white]excluding stocks: [green]{excluded_stocks}[/green]" if excluded_stocks != [""] else ""
    exclude_funds_text = f", [italic white]excluding funds: [blue]{excluded_funds}[/blue]" if excluded_funds != [""] else ""
    print(f"[italic white]Calculating profits" + exclude_stocks_part + exclude_funds_text + "...[/italic white]")

    
    # === READ & CONCAT ACCOUNT HISTORIES ===
    account_history = None
    for file_name in listdir("data"):
        if FILENAME_HINT in file_name:
            account_file_name = f"data/{file_name}"
            df = pd.read_excel(account_file_name).iloc[14:-7]  # Remove the info rows above and below
            
            df.columns = df.iloc[0]  # Update headers
            df = df.iloc[1:]  # Remove the header row from the data
            
            df = df.dropna(axis=1)  # Some column headers can still be None, remove those.

            if account_history is None:
                account_history = df
            else:
                account_history = pd.concat([account_history, df], ignore_index=True)

    account_history = account_history.drop_duplicates()

    # === CALCULATE PROFITS ===
    funds = create_funds(account_history, excluded_funds)
    fund_get_cache_out_profit = lambda cur : sum([f.net_money_spent.get_val(cur) for f in funds if f.count == 0])
    fund_get_cache_out_profit_display = lambda cur : get_currency_string(fund_get_cache_out_profit(cur), Currency.get_symbol(cur))

    fund_get_potential_fund_profit = lambda cur : sum([f.get_est_profit(cur) if f.count > 0 else f.net_money_spent.get_val(cur) for f in funds])
    fund_get_potential_fund_profit_display = lambda cur : get_currency_string(fund_get_potential_fund_profit(cur), Currency.get_symbol(cur))
    funds.sort(key=lambda f: -f.get_est_profit())  # Sort funds by profit

    stocks = get_stocks(account_history, excluded_stocks)
    stock_get_cache_out_profit = lambda cur : sum([s.net_money_spent.get_val(cur) for s in stocks if s.count == 0])
    stock_get_cache_out_profit_display = lambda cur : get_currency_string(stock_get_cache_out_profit(cur), Currency.get_symbol(cur))
    
    stock_get_potential_fund_profit = lambda cur : sum([s.get_est_profit(cur) if s.count > 0 else s.net_money_spent.get_val(cur) for s in stocks])
    stock_get_potential_fund_profit_display = lambda cur : get_currency_string(stock_get_potential_fund_profit(cur), Currency.get_symbol(cur))
    stocks.sort(key=lambda s: -s.get_est_profit())  # Sort stocks by profit

    commisions = calculate_commisions(account_history)

    # === DISPLAY ===
    
    stocks_profits_table = Table()
    stocks_profits_table.add_column("Kod", justify="left", style="cyan", no_wrap=True)
    stocks_profits_table.add_column("İsim", style="magenta")
    stocks_profits_table.add_column("Potansiyel Getiri", justify="right", no_wrap=True)
    stocks_profits_table.add_column("Eldeki Adet", justify="center", no_wrap=True)
    for s in stocks:
        stocks_profits_table.add_row(s.code, s.get_name(), get_currency_string(s.get_est_profit()), str(s.count))

    print()
    print(
        Panel.fit(
            Group(
                "\n",
                stocks_profits_table,
                Panel(f"{stock_get_cache_out_profit_display(Currency.TRY)} (Dolar Bazında: {stock_get_cache_out_profit_display(Currency.USD)})", title="Toplam Getiri"),
                Panel(f"{stock_get_potential_fund_profit_display(Currency.TRY)} (Dolar Bazında: {stock_get_potential_fund_profit_display(Currency.USD)})", title="Potansiyel Getiri"),
            ),
            title="[bold]Hisse Senetleri[/bold]"
        )
    )

    fund_pot_profits_table = Table()
    fund_pot_profits_table.add_column("Kod", justify="left", style="cyan", no_wrap=True)
    fund_pot_profits_table.add_column("İsim", style="magenta")
    fund_pot_profits_table.add_column("Potansiyel Getiri", justify="right", no_wrap=True)
    fund_pot_profits_table.add_column("Eldeki Adet", justify="center", no_wrap=True)
    for f in funds:
        fund_pot_profits_table.add_row(f.code, f.get_name(), get_currency_string(f.get_est_profit()), str(f.count))

    print()
    print(
        Panel.fit(
            Group(
                "\n",
                fund_pot_profits_table,
                Panel(f"{fund_get_cache_out_profit_display(Currency.TRY)} (Dolar Bazında: {fund_get_cache_out_profit_display(Currency.USD)})", title="Toplam Getiri"),
                Panel(f"{fund_get_potential_fund_profit_display(Currency.TRY)} (Dolar Bazında: {fund_get_potential_fund_profit_display(Currency.USD)})", title="Potansiyel Getiri"),
            ),
            title="[bold]Fonlar[/bold]"
        )
    )

    total_commision_cost = Money(0, Currency.TRY)
    for v in commisions.values(): total_commision_cost += v["cost"]

    commisions_table = Table(show_footer=True)
    commisions_table.add_column("Kısaltma", "Toplam", justify="left", style="cyan", no_wrap=True)
    commisions_table.add_column("İsim", style="magenta")
    commisions_table.add_column("Gider (₺)", get_currency_string(total_commision_cost.get_val(Currency.TRY)), justify="right", no_wrap=True)
    commisions_table.add_column("Gider ($)", get_currency_string(total_commision_cost.get_val(Currency.USD), "$"), justify="center", no_wrap=True)
    for k, v in commisions.items():
        commisions_table.add_row(k, v["name"], get_currency_string(v["cost"].get_val(Currency.TRY)), get_currency_string(v["cost"].get_val(Currency.USD), "$"))

    print()
    print(
        Panel.fit(
            Group(
                "\n",
                commisions_table,
            ),
            title="[bold]Vergiler ve Komisyon Ücretleri[/bold]"
        )
    )

    entire_data = {
        "Hisse Senetleri" : (stock_get_cache_out_profit(Currency.TRY), stock_get_potential_fund_profit(Currency.TRY), stock_get_cache_out_profit(Currency.USD), stock_get_potential_fund_profit(Currency.USD)),
        "Yatırım Fonları" : (fund_get_cache_out_profit(Currency.TRY), fund_get_potential_fund_profit(Currency.TRY), fund_get_cache_out_profit(Currency.USD), fund_get_potential_fund_profit(Currency.USD)),
        "Vergiler ve Komisyonlar" : (total_commision_cost.get_val(Currency.TRY), total_commision_cost.get_val(Currency.TRY), total_commision_cost.get_val(Currency.USD), total_commision_cost.get_val(Currency.USD))
    }
    
    entire_portfolio_table = Table(show_footer=True)
    entire_portfolio_table.add_column("Varlık", "Toplam", justify="left", style="cyan", no_wrap=True)
    entire_portfolio_table.add_column("Getiri (₺)", get_currency_string(sum([v[0] for v in entire_data.values()])), justify="left")
    entire_portfolio_table.add_column("Potansiyel Getiri (₺)", get_currency_string(sum([v[1] for v in entire_data.values()])), justify="left", no_wrap=True)
    entire_portfolio_table.add_column("Getiri ($)", get_currency_string(sum([v[2] for v in entire_data.values()]), "$"), justify="right")
    entire_portfolio_table.add_column("Potansiyel Getiri ($)", get_currency_string(sum([v[3] for v in entire_data.values()]), "$"), justify="right", no_wrap=True)
    
    for k, v in entire_data.items():
        entire_portfolio_table.add_row(k, get_currency_string(v[0]), get_currency_string(v[1]), get_currency_string(v[2], "$"), get_currency_string(v[3], "$"))

    print()
    print(
        Panel.fit(
            Group(
                "\n",
                entire_portfolio_table,
            ),
            title="[bold]Tüm Portföy[/bold]"
        )
    )

    print(f"""\n\n[italic][bold]Not:[/bold] "Toplam Kazanç" ile ifade edilen miktar, tamamen elden çıkartılmış olan
varlıklardan elde edilen net kazancı ifade eder. "Potansiyel Kazanç" ise elde tutulan
varlıkların, en son bilinen fiyatları üzerinden hesaplanan toplam değerini ifade eder.
Bu değer hesaplanırken bazı vergiler ve komisyonlar dikkate alınmamıştır.
""")
