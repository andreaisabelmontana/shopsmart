"""ShopSmart: a basket-optimization engine over a multi-store price catalog.

Public API:
    Catalog, Offer                     -- the catalog model + unit-price normalization
    single_store_totals, best_single_store
    per_item_cheapest                  -- unconstrained lower bound
    best_constrained_split             -- exact ≤k-store optimizer with trip cost
    brute_force_split                  -- reference solver (tests)
    demo_catalog, sample_shopping_list -- committed synthetic data
"""

from .catalog import Catalog, Offer, to_base_quantity
from .data import demo_catalog, sample_shopping_list
from .optimizer import (
    SplitPlan,
    StoreTotal,
    best_constrained_split,
    best_single_store,
    brute_force_split,
    per_item_cheapest,
    single_store_totals,
)

__all__ = [
    "Catalog",
    "Offer",
    "to_base_quantity",
    "StoreTotal",
    "SplitPlan",
    "single_store_totals",
    "best_single_store",
    "per_item_cheapest",
    "best_constrained_split",
    "brute_force_split",
    "demo_catalog",
    "sample_shopping_list",
]

__version__ = "1.0.0"
