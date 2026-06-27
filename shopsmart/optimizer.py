"""Basket optimization over a catalog.

Three problems, increasing in difficulty:

1. Single-store optimum
   For a shopping list, total each store's basket (handling items the store
   doesn't carry) and rank stores cheapest-first.

2. Per-item-cheapest split (unconstrained lower bound)
   Buy each item wherever it is cheapest, ignoring how many stores that implies.
   This is a true lower bound on item cost, but visiting every store is rarely
   practical -- so it's the *optimistic* benchmark, not a real plan.

3. Constrained ≤k-store split (the real optimization)
   Buy the whole list visiting at most `k` stores, paying a fixed `visit_cost`
   per store actually visited. This trades item savings against trips. Solved
   *exactly* by enumerating store subsets of size ≤ k: for a fixed set of stores,
   each item is bought at the cheapest store in the set that carries it, so
   scoring a subset is easy; we pick the best subset. We also expose a brute-force
   solver over all assignments for tests to verify against.

A "shopping list" is a dict {product: quantity}. Quantity is the number of packs
of that product to buy (the catalog's `price` is per pack).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product as iproduct
from math import inf

from .catalog import Catalog

ShoppingList = dict[str, float]


@dataclass
class StoreTotal:
    store: str
    total: float
    missing: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.missing


@dataclass
class SplitPlan:
    """An assignment of each item to a store, with the resulting cost breakdown."""

    assignment: dict[str, str]      # product -> store
    item_cost: float                # sum of item prices (no trip costs)
    visit_cost: float               # visit_cost * number of distinct stores
    missing: list[str] = field(default_factory=list)

    @property
    def stores_used(self) -> list[str]:
        return sorted(set(self.assignment.values()))

    @property
    def num_stores(self) -> int:
        return len(self.stores_used)

    @property
    def total(self) -> float:
        return self.item_cost + self.visit_cost


# --------------------------------------------------------------------------- #
# 1. Single-store ranking
# --------------------------------------------------------------------------- #

def single_store_totals(catalog: Catalog, shopping_list: ShoppingList) -> list[StoreTotal]:
    """Total each store's basket and rank cheapest-first.

    A store that is missing any item is still totalled over the items it *does*
    carry, but its `missing` list is populated; complete stores rank ahead of
    incomplete ones at the same price so a fully-stocked store is preferred.
    """
    results: list[StoreTotal] = []
    for store in catalog.stores:
        total = 0.0
        missing: list[str] = []
        for product, qty in shopping_list.items():
            price = catalog.price(store, product)
            if price is None:
                missing.append(product)
            else:
                total += price * qty
        results.append(StoreTotal(store=store, total=round(total, 2), missing=missing))
    # cheapest first; among equal, complete baskets win; then store name for determinism
    results.sort(key=lambda r: (not r.complete, r.total, r.store))
    return results


def best_single_store(catalog: Catalog, shopping_list: ShoppingList) -> StoreTotal:
    """Cheapest store that can supply the *entire* list; if none is complete,
    fall back to the cheapest store overall (with its missing items flagged)."""
    ranked = single_store_totals(catalog, shopping_list)
    complete = [r for r in ranked if r.complete]
    return complete[0] if complete else ranked[0]


# --------------------------------------------------------------------------- #
# 2. Per-item-cheapest split (unconstrained)
# --------------------------------------------------------------------------- #

def per_item_cheapest(
    catalog: Catalog, shopping_list: ShoppingList, visit_cost: float = 0.0
) -> SplitPlan:
    """Buy each item at its globally cheapest store. Unconstrained lower bound.

    `visit_cost` is included in the returned plan's total for honest comparison,
    but it does *not* influence the assignment -- this is purely per-item min.
    """
    assignment: dict[str, str] = {}
    item_cost = 0.0
    missing: list[str] = []
    for product, qty in shopping_list.items():
        best_store = None
        best_price = inf
        for store in catalog.stores:
            price = catalog.price(store, product)
            if price is not None and price < best_price:
                best_price = price
                best_store = store
        if best_store is None:
            missing.append(product)
            continue
        assignment[product] = best_store
        item_cost += best_price * qty
    n_stores = len({s for s in assignment.values()})
    return SplitPlan(
        assignment=assignment,
        item_cost=round(item_cost, 2),
        visit_cost=round(visit_cost * n_stores, 2),
        missing=missing,
    )


# --------------------------------------------------------------------------- #
# 3. Constrained ≤k-store split (exact, via subset enumeration)
# --------------------------------------------------------------------------- #

def _score_store_set(
    catalog: Catalog,
    shopping_list: ShoppingList,
    stores: tuple[str, ...],
    visit_cost: float,
) -> SplitPlan | None:
    """Best plan when shopping is restricted to exactly the given `stores`.

    Each item goes to the cheapest store *in the set* that carries it. Returns
    None if some item is carried by none of these stores (set can't fulfil list).
    The visit cost counts only stores that end up with at least one item.
    """
    assignment: dict[str, str] = {}
    item_cost = 0.0
    for product, qty in shopping_list.items():
        best_store = None
        best_price = inf
        for store in stores:
            price = catalog.price(store, product)
            if price is not None and price < best_price:
                best_price = price
                best_store = store
        if best_store is None:
            return None  # this subset cannot fulfil the whole list
        assignment[product] = best_store
        item_cost += best_price * qty
    used = {s for s in assignment.values()}
    return SplitPlan(
        assignment=assignment,
        item_cost=round(item_cost, 2),
        visit_cost=round(visit_cost * len(used), 2),
        missing=[],
    )


def best_constrained_split(
    catalog: Catalog,
    shopping_list: ShoppingList,
    max_stores: int = 2,
    visit_cost: float = 0.0,
) -> SplitPlan:
    """Cheapest plan that visits at most `max_stores` stores, paying `visit_cost`
    per store visited. Exact, by enumerating all store subsets of size ≤ k.

    Why this is exact: for any fixed set of stores you may visit, the cheapest
    fulfilment buys every item at the cheapest store in that set -- there is no
    interaction between items. So the optimum over "visit ≤ k stores" is just the
    best over all such subsets, which we enumerate. Total cost balances item cost
    against `visit_cost * (stores actually used)`.

    Raises ValueError if no subset of ≤ k stores can supply the whole list.
    """
    if max_stores < 1:
        raise ValueError("max_stores must be >= 1")
    stores = catalog.stores
    max_stores = min(max_stores, len(stores))

    best: SplitPlan | None = None
    for k in range(1, max_stores + 1):
        for subset in combinations(stores, k):
            plan = _score_store_set(catalog, shopping_list, subset, visit_cost)
            if plan is None:
                continue
            if best is None or plan.total < best.total - 1e-9:
                best = plan
    if best is None:
        raise ValueError(
            f"no combination of <= {max_stores} stores can supply the whole list"
        )
    return best


# --------------------------------------------------------------------------- #
# Brute-force reference (for tests): try every item->store assignment
# --------------------------------------------------------------------------- #

def brute_force_split(
    catalog: Catalog,
    shopping_list: ShoppingList,
    max_stores: int | None = None,
    visit_cost: float = 0.0,
) -> SplitPlan:
    """Exhaustively search every item->store assignment (exponential).

    For each product, the choices are the stores that carry it. We try the full
    Cartesian product of choices, skip assignments that use more than
    `max_stores` distinct stores, and keep the cheapest total. Used only to
    validate `best_constrained_split` on small instances.
    """
    products = list(shopping_list.keys())
    choices: list[list[str]] = []
    for p in products:
        carriers = [s for s in catalog.stores if catalog.price(s, p) is not None]
        if not carriers:
            raise ValueError(f"no store carries {p!r}")
        choices.append(carriers)

    best: SplitPlan | None = None
    for combo in iproduct(*choices):
        used = set(combo)
        if max_stores is not None and len(used) > max_stores:
            continue
        assignment = dict(zip(products, combo))
        item_cost = sum(
            catalog.price(assignment[p], p) * shopping_list[p] for p in products
        )
        plan = SplitPlan(
            assignment=assignment,
            item_cost=round(item_cost, 2),
            visit_cost=round(visit_cost * len(used), 2),
            missing=[],
        )
        if best is None or plan.total < best.total - 1e-9:
            best = plan
    if best is None:
        raise ValueError(
            f"no assignment uses <= {max_stores} stores for the whole list"
        )
    return best
