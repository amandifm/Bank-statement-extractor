import re
from typing import Optional

def _parse_amount(s: str) -> Optional[float]:
    s = s.replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None

def test_logic(val1, val2, previous_balance):
    debit = None
    credit = None
    balance = None
    
    # Try to see if val2 is a balance
    if previous_balance is not None:
        if abs(previous_balance - val1 - val2) < 0.01:
            # val1 is Debit, val2 is Balance
            debit = val1
            balance = val2
        elif abs(previous_balance + val1 - val2) < 0.01:
            # val1 is Credit, val2 is Balance
            credit = val1
            balance = val2
            
    if balance is None:
        # Default fallback
        debit = val1
        credit = val2
        
    print(f"val1={val1}, val2={val2}, prev={previous_balance} -> debit={debit}, credit={credit}, balance={balance}")

test_logic(5910.64, 25906.77, 19996.13)
test_logic(14085.49, 5910.64, 19996.13)
