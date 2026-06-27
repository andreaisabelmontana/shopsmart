"""Catalog model: stores, products, prices, pack sizes, and unit-price normalization.

A catalog is a flat table of offers. Each offer says:
    "store S sells product P, in a pack of `pack_size` `unit`, for `price`."

From that table we derive:
  - the price of any product at any store (the cheapest qualifying pack),
  - a normalized *unit price* (price per kg / per litre / per each) so packs of
    different sizes can be compared fairly.

The data is deliberately small and human-readable so the optimizer's answers can
be checked by hand. A larger, clearly-synthetic catalog lives in `data.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

# Canonical base units. Every pack is normalized to one of these so that, e.g.,
# a 500 g pack and a 1 kg pack of the same product are directly comparable.
#   mass    -> kilogram (kg)
#   volume  -> litre (l)
#   count   -> each (ea)
_MASS = {"g": 0.001, "kg": 1.0}
_VOLUME = {"ml": 0.001, "l": 1.0}
_COUNT = {"ea": 1.0, "unit": 1.0, "pack": 1.0}

_BASE_UNIT = {**{u: "kg" for u in _MASS}, **{u: "l" for u in _VOLUME}, **{u: "ea" for u in _COUNT}}
_TO_BASE = {**_MASS, **_VOLUME, **_COUNT}


def to_base_quantity(pack_size: float, unit: str) -> tuple[float, str]:
    """Convert a pack size in `unit` to its canonical base unit.

    >>> to_base_quantity(500, "g")
    (0.5, 'kg')
    >>> to_base_quantity(2, "l")
    (2.0, 'l')
    """
    unit = unit.lower().strip()
    if unit not in _TO_BASE:
        raise ValueError(f"unknown unit {unit!r}; known units: {sorted(_TO_BASE)}")
    return pack_size * _TO_BASE[unit], _BASE_UNIT[unit]


@dataclass(frozen=True)
class Offer:
    """One (store, product, pack) row of the catalog."""

    store: str
    product: str
    price: float          # price for the whole pack, in currency units (e.g. EUR)
    pack_size: float = 1.0
    unit: str = "ea"

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError(f"negative price for {self.product} @ {self.store}")
        if self.pack_size <= 0:
            raise ValueError(f"non-positive pack size for {self.product} @ {self.store}")

    @property
    def base_quantity(self) -> float:
        """Pack size expressed in the canonical base unit (kg / l / ea)."""
        return to_base_quantity(self.pack_size, self.unit)[0]

    @property
    def base_unit(self) -> str:
        return to_base_quantity(self.pack_size, self.unit)[1]

    @property
    def unit_price(self) -> float:
        """Price per base unit (per kg / per litre / per each)."""
        return self.price / self.base_quantity


class Catalog:
    """A queryable collection of offers across stores.

    The catalog answers two core questions for the optimizer:
      - `price(store, product)`  -> cheapest pack price for that product at that
        store, or None if the store does not carry it.
      - `best_unit_value(product)` -> the offer with the lowest price-per-base-unit
        for a product, anywhere (used for fair pack-size comparisons).
    """

    def __init__(self, offers: Iterable[Offer]):
        self.offers: list[Offer] = list(offers)
        if not self.offers:
            raise ValueError("catalog is empty")
        self._stores = sorted({o.store for o in self.offers})
        self._products = sorted({o.product for o in self.offers})

    # -- construction helpers ------------------------------------------------

    @classmethod
    def from_rows(cls, rows: Iterable[dict]) -> "Catalog":
        return cls(Offer(**row) for row in rows)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "Catalog":
        cols = {"store", "product", "price"}
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"dataframe missing columns: {sorted(missing)}")
        offers = []
        for r in df.to_dict("records"):
            offers.append(
                Offer(
                    store=r["store"],
                    product=r["product"],
                    price=float(r["price"]),
                    pack_size=float(r.get("pack_size", 1.0)),
                    unit=str(r.get("unit", "ea")),
                )
            )
        return cls(offers)

    # -- accessors -----------------------------------------------------------

    @property
    def stores(self) -> list[str]:
        return list(self._stores)

    @property
    def products(self) -> list[str]:
        return list(self._products)

    def offers_for(self, product: str, store: str | None = None) -> list[Offer]:
        return [
            o
            for o in self.offers
            if o.product == product and (store is None or o.store == store)
        ]

    def price(self, store: str, product: str) -> float | None:
        """Cheapest pack price for `product` at `store`, or None if not carried.

        If a store stocks multiple packs of the same product we take the cheapest
        whole-pack price (a shopper buying one unit of the item pays the least).
        """
        candidates = [o.price for o in self.offers_for(product, store)]
        return min(candidates) if candidates else None

    def cheapest_offer(self, store: str, product: str) -> Offer | None:
        candidates = self.offers_for(product, store)
        return min(candidates, key=lambda o: o.price) if candidates else None

    def best_unit_value(self, product: str) -> Offer | None:
        """The offer with the lowest price per base unit for `product`, anywhere.

        This is the fair "best value" pick: it accounts for pack size, so a
        cheaper-looking small pack can lose to a larger pack with a lower
        price-per-kg.
        """
        candidates = self.offers_for(product)
        return min(candidates, key=lambda o: o.unit_price) if candidates else None

    def price_matrix(self) -> pd.DataFrame:
        """products x stores matrix of cheapest pack prices (NaN where missing)."""
        data = {
            store: [self.price(store, p) for p in self._products]
            for store in self._stores
        }
        return pd.DataFrame(data, index=self._products)
