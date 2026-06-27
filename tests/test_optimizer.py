"""Tests with hand-computed expected answers, plus brute-force cross-checks."""

from __future__ import annotations

import random

import pytest

from shopsmart import (
    Catalog,
    Offer,
    best_constrained_split,
    best_single_store,
    brute_force_split,
    demo_catalog,
    per_item_cheapest,
    single_store_totals,
)
from shopsmart.optimizer import _score_store_set  # noqa: F401  (internal, exercised indirectly)


# --------------------------------------------------------------------------- #
# A tiny hand-built catalog whose every answer can be checked on paper.
#
#            A      B      C
#  Milk     1.00   1.20   0.90
#  Bread    2.00   1.50   1.80
#  Eggs     3.00   3.50   2.50
#  Apples   1.00   0.80    -     (C does not carry Apples)
# --------------------------------------------------------------------------- #
def tiny_catalog() -> Catalog:
    return Catalog(
        [
            Offer("A", "Milk", 1.00), Offer("B", "Milk", 1.20), Offer("C", "Milk", 0.90),
            Offer("A", "Bread", 2.00), Offer("B", "Bread", 1.50), Offer("C", "Bread", 1.80),
            Offer("A", "Eggs", 3.00), Offer("B", "Eggs", 3.50), Offer("C", "Eggs", 2.50),
            Offer("A", "Apples", 1.00), Offer("B", "Apples", 0.80),
        ]
    )


LIST = {"Milk": 1, "Bread": 1, "Eggs": 1, "Apples": 1}


# --- 1. single-store ranking ------------------------------------------------ #

def test_single_store_ranking_known_answer():
    cat = tiny_catalog()
    ranked = single_store_totals(cat, LIST)
    # Totals over the items each store carries:
    #   A: 1.00 + 2.00 + 3.00 + 1.00 = 7.00  (complete)
    #   B: 1.20 + 1.50 + 3.50 + 0.80 = 7.00  (complete)
    #   C: 0.90 + 1.80 + 2.50        = 5.20  (missing Apples)
    totals = {r.store: r.total for r in ranked}
    assert totals == {"A": 7.00, "B": 7.00, "C": 5.20}

    # C is cheaper but incomplete; best complete single store is a tie A/B at 7.00,
    # broken deterministically by store name -> A.
    best = best_single_store(cat, LIST)
    assert best.store == "A"
    assert best.total == 7.00
    assert best.complete

    # Ranking puts complete stores before the incomplete-but-cheaper C.
    assert [r.store for r in ranked] == ["A", "B", "C"]
    assert ranked[-1].store == "C" and ranked[-1].missing == ["Apples"]


# --- 2. per-item-cheapest split = known minimum ----------------------------- #

def test_per_item_cheapest_equals_known_minimum():
    cat = tiny_catalog()
    plan = per_item_cheapest(cat, LIST)
    # Cheapest per item:
    #   Milk  -> C 0.90
    #   Bread -> B 1.50
    #   Eggs  -> C 2.50
    #   Apples-> B 0.80
    # item cost = 0.90 + 1.50 + 2.50 + 0.80 = 5.70
    assert plan.assignment == {"Milk": "C", "Bread": "B", "Eggs": "C", "Apples": "B"}
    assert plan.item_cost == 5.70
    assert set(plan.stores_used) == {"B", "C"}
    assert plan.missing == []


def test_per_item_cheapest_is_a_lower_bound():
    cat = demo_catalog()
    from shopsmart import sample_shopping_list

    sl = sample_shopping_list()
    lb = per_item_cheapest(cat, sl).item_cost
    # No single store and no constrained plan can beat the per-item-cheapest item cost.
    best_store = best_single_store(cat, sl)
    assert best_store.total >= lb - 1e-9
    for k in (1, 2, 3, 4):
        plan = best_constrained_split(cat, sl, max_stores=k, visit_cost=0.0)
        assert plan.item_cost >= lb - 1e-9


# --- 3. constrained ≤k optimizer = proven optimum (vs brute force) ---------- #

def test_constrained_split_matches_brute_force_no_trip_cost():
    cat = tiny_catalog()
    # With no trip cost, the ≤3-store optimum must equal the per-item minimum 5.70.
    plan = best_constrained_split(cat, LIST, max_stores=3, visit_cost=0.0)
    bf = brute_force_split(cat, LIST, max_stores=3, visit_cost=0.0)
    assert plan.total == bf.total == 5.70


def test_constrained_split_two_store_known_answer():
    cat = tiny_catalog()
    # Restrict to <=2 stores, no trip cost.
    # Best 2-store set is {B,C}: Milk C .90, Bread B 1.50, Eggs C 2.50, Apples B .80 = 5.70.
    # (Same as unconstrained because the per-item optimum only used B and C.)
    plan = best_constrained_split(cat, LIST, max_stores=2, visit_cost=0.0)
    assert plan.total == 5.70
    assert set(plan.stores_used) == {"B", "C"}


def test_trip_cost_pushes_toward_fewer_stores():
    cat = tiny_catalog()
    # Big trip cost makes a one-store plan win even though items cost more.
    # Single store totals: A 7.00, B 7.00, C incomplete (can't fulfil Apples).
    # With visit_cost=5: one store -> 7.00 + 5 = 12.00; two stores {B,C} -> 5.70 + 10 = 15.70.
    plan = best_constrained_split(cat, LIST, max_stores=2, visit_cost=5.0)
    assert plan.num_stores == 1
    assert plan.total == 12.00
    assert set(plan.stores_used) in ({"A"}, {"B"})  # tie at 12.00, either is optimal

    bf = brute_force_split(cat, LIST, max_stores=2, visit_cost=5.0)
    assert plan.total == bf.total


def test_constrained_matches_brute_force_randomized():
    rng = random.Random(20260627)
    for _ in range(60):
        stores = [f"S{i}" for i in range(rng.randint(2, 5))]
        products = [f"P{i}" for i in range(rng.randint(2, 6))]
        offers = []
        for p in products:
            # ensure every product is carried by at least one store
            carriers = rng.sample(stores, rng.randint(1, len(stores)))
            for s in carriers:
                offers.append(Offer(s, p, round(rng.uniform(0.5, 9.5), 2)))
        cat = Catalog(offers)
        sl = {p: rng.randint(1, 3) for p in products}
        visit = rng.choice([0.0, 0.5, 1.0, 3.0])
        for k in range(1, len(stores) + 1):
            # brute force over the same <=k constraint. Some k may be infeasible
            # (no <=k-store subset can fulfil the list); both solvers must agree
            # by raising in that case.
            try:
                bf = brute_force_split(cat, sl, max_stores=k, visit_cost=visit)
            except ValueError:
                with pytest.raises(ValueError):
                    best_constrained_split(cat, sl, max_stores=k, visit_cost=visit)
                continue
            got = best_constrained_split(cat, sl, max_stores=k, visit_cost=visit)
            assert got.total == pytest.approx(bf.total), (
                f"mismatch k={k} visit={visit}: {got.total} vs {bf.total}"
            )


# --- 4. unit-price normalization picks better value across pack sizes ------- #

def test_unit_price_normalization_picks_better_value():
    # Store X: 500 g coffee for 4.00  -> 8.00 / kg
    # Store Y: 1 kg coffee for 7.00    -> 7.00 / kg  (cheaper per kg despite higher sticker)
    cat = Catalog(
        [
            Offer("X", "Coffee", 4.00, pack_size=500, unit="g"),
            Offer("Y", "Coffee", 7.00, pack_size=1, unit="kg"),
        ]
    )
    best = cat.best_unit_value("Coffee")
    assert best.store == "Y"
    assert best.unit_price == pytest.approx(7.00)   # per kg
    # The naive sticker-price min would wrongly pick X at 4.00.
    assert cat.price("X", "Coffee") == 4.00
    assert cat.price("Y", "Coffee") == 7.00


def test_unit_price_across_volume_units():
    # 750 ml olive oil 5.90 -> 7.8667/l ; 1 l for 6.20 -> 6.20/l (better value)
    cat = Catalog(
        [
            Offer("A", "Olive Oil", 5.90, pack_size=750, unit="ml"),
            Offer("B", "Olive Oil", 6.20, pack_size=1, unit="l"),
        ]
    )
    best = cat.best_unit_value("Olive Oil")
    assert best.store == "B"
    assert best.unit_price == pytest.approx(6.20)


# --- 5. missing-item handling ----------------------------------------------- #

def test_missing_item_flagged_in_single_store():
    cat = tiny_catalog()  # C has no Apples
    ranked = {r.store: r for r in single_store_totals(cat, LIST)}
    assert ranked["C"].missing == ["Apples"]
    assert not ranked["C"].complete
    assert ranked["A"].complete and ranked["A"].missing == []


def test_missing_item_in_per_item_split():
    # Nobody carries "Caviar": it should land in `missing`, not crash.
    cat = tiny_catalog()
    sl = {"Milk": 1, "Caviar": 1}
    plan = per_item_cheapest(cat, sl)
    assert plan.missing == ["Caviar"]
    assert plan.assignment == {"Milk": "C"}
    assert plan.item_cost == 0.90


def test_constrained_split_raises_when_unfulfillable():
    cat = tiny_catalog()
    # Apples only at A and B; restrict to {C}-only is impossible, but with max=1
    # the solver should still find a single store... none is complete, so it raises.
    sl = {"Milk": 1, "Apples": 1}
    # With max_stores=1: A has both (1.00+1.00), B has both (1.20+0.80). Fulfillable.
    plan = best_constrained_split(cat, sl, max_stores=1, visit_cost=0.0)
    assert plan.num_stores == 1
    # Now a list with an item nobody carries -> unfulfillable at any k.
    with pytest.raises(ValueError):
        best_constrained_split(cat, {"Caviar": 1}, max_stores=2)


# --- demo catalog sanity ----------------------------------------------------- #

def test_demo_catalog_structure():
    cat = demo_catalog()
    assert set(cat.stores) == {"FreshCo", "MartMax", "GreenBasket", "ValuMart"}
    assert len(cat.products) == 20
    # price matrix has the expected shape and some NaNs (intentional gaps).
    pm = cat.price_matrix()
    assert pm.shape == (20, 4)
    assert pm.isna().to_numpy().sum() > 0
