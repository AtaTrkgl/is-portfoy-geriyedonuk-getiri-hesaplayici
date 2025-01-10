from utilities import parse_currency_text
from constants import *
from money import Money, Currency

import pandas as pd
from datetime import datetime

TAXES_CODE = "ST"  # BSMV & MSİGV
KEEPING_CODE = "QM"  # YAT.HS.SAKLAMA ÜCRETİ

def calculate_commisions(history: pd.DataFrame) -> dict:
    bsmv_cost = Money(0, Currency.TRY)
    yhsu_cost = Money(0, Currency.TRY)
    msigv_cost = Money(0, Currency.TRY)

    for i in reversed(range(len(history))):
        row = history.iloc[i]

        action_type = row[OP_TYPE_COL]
        cost = Money(row[COST_COL], Currency.TRY, datetime.strptime(row[DATETIME_COL], r"%d/%m/%Y-%H:%M:%S"))
        
        if TAXES_CODE in action_type:
            desc = row[DESC_COL]
            if "MSİGV" in desc:
                msigv_cost += cost
            elif "BSMV" in desc:
                bsmv_cost += cost
        elif KEEPING_CODE in action_type:
            yhsu_cost += cost

    return {
        "BSMV": {
            "cost": bsmv_cost,
            "name": "Banka Sigorta Muamele Vergisi"
        },
        "YHSÜ": {
            "cost": yhsu_cost,
            "name": "Yatırım Hesabı Saklama Ücreti"
        },
        "MSİGV": {
            "cost": msigv_cost,
            "name": "Menkul Sermaye İradı Gelir Vergisi"
        }
    }
