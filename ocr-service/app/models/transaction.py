from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Transaction:
    id: str
    date: str
    description: str
    debit: Optional[float]
    credit: Optional[float]
    balance: Optional[float]
    type: str
    confidence: float
    raw_text: str
    page: int

    def to_dict(self) -> dict:
        data = asdict(self)
        data["debit_display"] = format_money(self.debit)
        data["credit_display"] = format_money(self.credit)
        data["balance_display"] = format_money(self.balance)
        data["confidence_display"] = f"{round(self.confidence * 100)}%"
        return data


def format_money(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"
