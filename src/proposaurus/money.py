"""Currency formatting.

The numeric format is Anglo (1,234.56) in every currency: it is unambiguous,
and mixing separator conventions across a set of proposals is worse than
picking one. The currency only chooses the prefix symbol; nothing converts.
"""

from __future__ import annotations

from collections.abc import Callable

# Currency code -> prefix symbol. Unknown codes fall back to "CODE ".
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}

Amount = float | int | str | None


def symbol_for(currency: str) -> str:
    """Prefix symbol for a currency code, falling back to the code itself."""
    return CURRENCY_SYMBOLS.get(currency.upper(), f"{currency.upper()} ")


def format_money(value: Amount, currency: str = "USD") -> str:
    """``4500.0`` -> ``"$4,500.00"`` (USD) or ``"€4,500.00"`` (EUR).

    ``None`` formats as the empty string, so an optional price renders blank.
    """
    if value is None:
        return ""
    return f"{symbol_for(currency)}{float(value):,.2f}"


def money_parts(value: Amount, currency: str = "USD") -> tuple[str, str, str] | None:
    """Split an amount into ``(symbol, whole, cents)`` for a template to lay out.

    ``1234.5`` -> ``("$", "1,234", "50")``. Use it when a brand sets the cents
    differently from the rest of the figure. ``None`` gives ``None``.
    """
    if value is None:
        return None
    whole, cents = f"{float(value):,.2f}".split(".")
    return symbol_for(currency), whole, cents


def make_money(currency: str = "USD") -> Callable[[Amount], str]:
    """A one-argument ``money`` formatter bound to ``currency``, for a Jinja filter."""

    def money(value: Amount) -> str:
        return format_money(value, currency)

    return money
