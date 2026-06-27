"""A committed, clearly-SYNTHETIC catalog: 4 supermarkets x 20 products.

All store names and prices are invented for demonstration. They are *not* scraped
from, nor intended to represent, any real retailer. Prices are plausible EUR
values with deliberate cross-store variation and a few intentional gaps (not
every store stocks every product) so the optimizer has something real to chew on.

Pack sizes vary across stores for the same product, which is what makes
unit-price normalization meaningful (see `Catalog.best_unit_value`).
"""

from __future__ import annotations

from .catalog import Catalog, Offer

# store, product, price (EUR), pack_size, unit
_ROWS = [
    # --- FreshCo: a touch pricier, full range, often larger packs -----------
    ("FreshCo", "Milk",            1.10, 1, "l"),
    ("FreshCo", "Bread",           1.40, 800, "g"),
    ("FreshCo", "Eggs",            2.60, 12, "ea"),
    ("FreshCo", "Bananas",         1.20, 1, "kg"),
    ("FreshCo", "Coffee",          3.90, 250, "g"),
    ("FreshCo", "Rice",            3.40, 2, "kg"),
    ("FreshCo", "Chicken",         5.50, 1, "kg"),
    ("FreshCo", "Pasta",           0.95, 500, "g"),
    ("FreshCo", "Tomatoes",        1.80, 1, "kg"),
    ("FreshCo", "Cheese",          3.20, 250, "g"),
    ("FreshCo", "Butter",          1.95, 250, "g"),
    ("FreshCo", "Apples",          2.10, 1, "kg"),
    ("FreshCo", "Orange Juice",    2.30, 1, "l"),
    ("FreshCo", "Cereal",          2.80, 500, "g"),
    ("FreshCo", "Yogurt",          1.60, 500, "g"),
    ("FreshCo", "Olive Oil",       6.50, 1, "l"),
    ("FreshCo", "Sugar",           1.20, 1, "kg"),
    ("FreshCo", "Flour",           1.10, 1, "kg"),
    ("FreshCo", "Tea",             2.40, 100, "g"),
    ("FreshCo", "Salmon",          7.80, 500, "g"),

    # --- MartMax: aggressive on staples, smaller packs, missing a few items --
    ("MartMax", "Milk",            0.95, 1, "l"),
    ("MartMax", "Bread",           1.55, 1000, "g"),
    ("MartMax", "Eggs",            2.40, 12, "ea"),
    ("MartMax", "Bananas",         1.15, 1, "kg"),
    ("MartMax", "Coffee",          4.20, 250, "g"),
    ("MartMax", "Rice",            1.70, 1, "kg"),
    ("MartMax", "Chicken",         5.20, 1, "kg"),
    ("MartMax", "Pasta",           1.05, 500, "g"),
    ("MartMax", "Tomatoes",        1.65, 1, "kg"),
    ("MartMax", "Cheese",          2.95, 200, "g"),
    ("MartMax", "Butter",          2.10, 250, "g"),
    ("MartMax", "Apples",          1.90, 1, "kg"),
    # MartMax does not stock Orange Juice or Salmon
    ("MartMax", "Cereal",          2.50, 375, "g"),
    ("MartMax", "Yogurt",          1.45, 500, "g"),
    ("MartMax", "Olive Oil",       5.90, 750, "ml"),
    ("MartMax", "Sugar",           1.05, 1, "kg"),
    ("MartMax", "Flour",           0.99, 1, "kg"),
    ("MartMax", "Tea",             2.60, 100, "g"),

    # --- GreenBasket: cheap fresh/own-brand, premium on some packaged goods --
    ("GreenBasket", "Milk",         1.05, 1, "l"),
    ("GreenBasket", "Bread",        1.30, 800, "g"),
    ("GreenBasket", "Eggs",         2.75, 12, "ea"),
    ("GreenBasket", "Bananas",      1.10, 1, "kg"),
    ("GreenBasket", "Coffee",       3.70, 250, "g"),
    ("GreenBasket", "Rice",         1.90, 1, "kg"),
    ("GreenBasket", "Chicken",      5.80, 1, "kg"),
    ("GreenBasket", "Pasta",        0.90, 500, "g"),
    ("GreenBasket", "Tomatoes",     1.50, 1, "kg"),
    ("GreenBasket", "Cheese",       3.40, 250, "g"),
    ("GreenBasket", "Butter",       1.85, 250, "g"),
    ("GreenBasket", "Apples",       1.75, 1, "kg"),
    ("GreenBasket", "Orange Juice", 2.10, 1, "l"),
    ("GreenBasket", "Cereal",       3.10, 500, "g"),
    ("GreenBasket", "Yogurt",       1.55, 500, "g"),
    ("GreenBasket", "Olive Oil",    6.20, 1, "l"),
    ("GreenBasket", "Sugar",        1.15, 1, "kg"),
    ("GreenBasket", "Flour",        1.05, 1, "kg"),
    ("GreenBasket", "Tea",          2.30, 100, "g"),
    ("GreenBasket", "Salmon",       7.40, 500, "g"),

    # --- ValuMart: discounter; bulk packs, lowest unit prices, gaps on fresh -
    ("ValuMart", "Milk",            0.99, 2, "l"),
    ("ValuMart", "Bread",           1.20, 750, "g"),
    ("ValuMart", "Eggs",            2.30, 12, "ea"),
    # ValuMart skips Bananas, Tomatoes, Apples (limited fresh produce)
    ("ValuMart", "Coffee",          7.20, 500, "g"),
    ("ValuMart", "Rice",            2.90, 2, "kg"),
    ("ValuMart", "Chicken",        10.20, 2, "kg"),
    ("ValuMart", "Pasta",           1.60, 1, "kg"),
    ("ValuMart", "Cheese",          5.40, 500, "g"),
    ("ValuMart", "Butter",          1.80, 250, "g"),
    ("ValuMart", "Orange Juice",    1.95, 1, "l"),
    ("ValuMart", "Cereal",          4.40, 750, "g"),
    ("ValuMart", "Yogurt",          2.40, 1000, "g"),
    ("ValuMart", "Olive Oil",       9.60, 2, "l"),
    ("ValuMart", "Sugar",           1.90, 2, "kg"),
    ("ValuMart", "Flour",           1.70, 2, "kg"),
    ("ValuMart", "Tea",             4.20, 200, "g"),
    ("ValuMart", "Salmon",         13.50, 1, "kg"),
]


def demo_catalog() -> Catalog:
    """The committed synthetic catalog used by the demo, tests, and the website."""
    return Catalog(
        Offer(store=s, product=p, price=price, pack_size=ps, unit=u)
        for (s, p, price, ps, u) in _ROWS
    )


def sample_shopping_list() -> dict[str, float]:
    """A representative weekly basket (product -> number of packs)."""
    return {
        "Milk": 2,
        "Bread": 1,
        "Eggs": 1,
        "Bananas": 1,
        "Coffee": 1,
        "Chicken": 1,
        "Pasta": 2,
        "Cheese": 1,
        "Orange Juice": 1,
        "Yogurt": 1,
    }
