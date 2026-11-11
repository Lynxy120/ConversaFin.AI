from typing import Any


def rupiah(v: Any) -> str:
    return "Rp" + f"{int(float(v)):,}".replace(",", ".")
