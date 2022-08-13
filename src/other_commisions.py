from utilities import currency_to_number

TAXES_CODE = "ST"
KEEPING_CODE = "QM"

def calculate_other_commisions(df) -> float:
    taxes_commisions = 0
    keeping_commisions = 0

    for i in reversed(range(1, len(df["İşlem"]) + 1)):
        action_type = df["İşlem"][i]
        
        if TAXES_CODE in action_type:
            taxes_commisions += currency_to_number(str(df["İşlem Tutarı"][i]), ".", ",")
        elif KEEPING_CODE in action_type:
            keeping_commisions += currency_to_number(str(df["İşlem Tutarı"][i]), ".", ",")

    return taxes_commisions, keeping_commisions
