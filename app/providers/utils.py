from math import isnan
from typing import Any


def first_value(row: dict[str, Any], aliases: tuple[str, ...], default: float = 0.0) -> float:
    for key in aliases:
        if key not in row:
            continue
        value = row[key]
        try:
            cleaned = str(value).replace(",", "").replace("%", "").strip()
            number = float(cleaned)
        except (TypeError, ValueError):
            continue
        if not isnan(number):
            return number
    return default


def clamp(value: float, low: float = -100.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def exchange_code(code: str) -> str:
    if code.startswith(("5", "6", "9")):
        return f"{code}.SH"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    return f"{code}.SZ"


def baostock_code(code: str) -> str:
    prefix = "sh" if code.startswith(("5", "6", "9")) else "bj" if code.startswith(("4", "8")) else "sz"
    return f"{prefix}.{code}"
