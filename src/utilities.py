
def parse_currency_text(currency: str, decimal_seperator: str=",", digit_seperator: str=".") -> float:
    currency_text = currency.replace("TRY", "").strip().replace(digit_seperator, "").replace(decimal_seperator, ".")
    
    return float(currency_text)

def add_to_dict(dictionary: dict, key: str, value: float):
    if key in dictionary:
        dictionary[key] += value
    else:
        dictionary[key] = value

def get_currency_string(val: float, currency_symbol: str="₺") -> str:
    color = ""
    sign = ""
    if val > 0:
        color = "bold green"
        sign = "+"
    elif val < 0:
        color = "bold red"
        sign = "-"
    else:
        color = "bold gray"

    return f"[{color}]{sign}{abs(val):,.2f}{currency_symbol}[/{color}]"
