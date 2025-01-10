from enum import Enum
from datetime import datetime, timedelta
from typing import Optional

import yfinance as yf

class Currency(Enum):
    USD = 1
    EUR = 2
    TRY = 3

    @staticmethod
    def from_str(currency: str):
        currency = currency.upper()
        if currency == "USD":
            return Currency.USD
        if currency == "EUR":
            return Currency.EUR
        if currency in ["TRY", "TL"]:
            return Currency.TRY
        
        raise ValueError(f"Invalid currency: {currency}")

    @staticmethod
    def get_symbol(currency) -> str:
        if currency is Currency.USD:
            return "$"
        if currency is Currency.EUR:
            return "€"
        if currency is Currency.TRY:
            return "₺"
        
        return ""

    @staticmethod
    def get_conversion_rate(f, t, date: Optional[datetime] = None) -> float:
        if f == t:
            return 1.0
        
        # Format the ticker symbol for yfinance
        ticker = f"{f.name}{t.name}=X"
        
        try:
            # Use provided date or current date
            end_date = (date or datetime.now()) + timedelta(days=1)
            start_date = end_date - timedelta(days=2)
            
            hist = yf.download(
                ticker, 
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if hist.empty:
                raise ValueError(f"No exchange rate data found for {ticker}")

            return hist['Close'].iloc[-1][0]
            
        except Exception as e:
            raise ValueError(f"Failed to convert {f.value} to {t.value}: {str(e)}")

class Money:
    def __init__(self, amount: int, currency: Currency = Currency.TRY, date: Optional[datetime] = None):
        self.amount = amount
        self.currency = currency
        self.date = date if date is not None else datetime.now()

    def __add__(self, other):
        converted_amount = other.amount * Currency.get_conversion_rate(
            other.currency, 
            self.currency,
            other.date
        )
        return Money(self.amount + converted_amount, self.currency, self.date)

    def __sub__(self, other):
        return self + Money(-other.amount, other.currency, other.date)

    def __mul__(self, c: float | int):
        return Money(self.amount * c, self.currency, self.date)

    def __rmul__(self, c: float | int):
        return self * c

    def __neg__(self):
        return Money(-self.amount, self.currency, self.date)

    def __repr__(self):
        return f"Money({self.amount}, {self.currency}, {self.date.strftime('%Y-%m-%d')})"

    def get_val(self, currency: Optional[Currency] = None) -> float:
        if currency is None or currency == self.currency:
            return self.amount
        
        return self.amount * Currency.get_conversion_rate(
            self.currency, 
            currency,
            self.date
        )
    
if __name__ == "__main__":
    # Example with different dates
    past_date = datetime(2023, 1, 1)
    current_date = datetime.now()
    
    m1 = Money(100, Currency.USD, past_date)
    m2 = Money(100, Currency.EUR, current_date)
    
    print(f"USD amount from {past_date.date()}: {m1}")
    print(f"Value in TRY: {m1.get_val(Currency.TRY)}")
    
    combined = m1 + m2
    print(f"Combined value in TRY: {combined.get_val(Currency.TRY)}")
    print(f"Combined value in USD: {combined.get_val(Currency.USD)}")
    print(f"Combined Money object: {combined}")