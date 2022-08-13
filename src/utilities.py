
def currency_to_number(currency: str, decimal_seperator: str=",", digit_seperator: str=".") -> float:
    currency_text = currency.replace("TRY", "").strip().replace(digit_seperator, "").replace(decimal_seperator, ".")
    
    return float(currency_text)

def add_to_dict(dictionary: dict, key: str, value: float):
    if key in dictionary:
        dictionary[key] += value
    else:
        dictionary[key] = value
