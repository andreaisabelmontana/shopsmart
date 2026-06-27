# ShopSmart

A basket-optimization engine over a multi-store price catalog. Given a shopping
list and a catalog of supermarket prices, it finds the cheapest way to shop —
either at a single store, or split across stores with a per-trip cost so the
savings have to beat the cost of an extra visit.

🔗 **Showcase site:** https://andreaisabelmontana.github.io/shopsmart/

The website is an in-browser illustration. The optimizer below is real Python
with a pytest suite; the website mirrors its logic over the same committed catalog.

## The catalog model

A catalog is a flat table of **offers**. Each offer is one row:

> store **S** sells product **P**, in a pack of `pack_size` `unit`, for `price`.

From that table the engine derives the price of any product at any store (the
cheapest qualifying pack) and a normalized **unit price** so packs of different
sizes can be compared fairly. The committed catalog in `shopsmart/data.py` is
**synthetic** — 4 invented supermarkets × 20 products, with deliberate price
variation, varied pack sizes, and a few intentional gaps (not every store stocks
every item). It does not represent any real retailer.

```python
from shopsmart import Catalog, Offer
cat = Catalog([
    Offer("FreshCo", "Coffee", 3.90, pack_size=250, unit="g"),
    Offer("ValuMart", "Coffee", 7.20, pack_size=500, unit="g"),
])
cat.price("FreshCo", "Coffee")        # 3.90  (cheapest pack at that store)
cat.best_unit_value("Coffee").store   # 'ValuMart'  -> 14.40 /kg beats 15.60 /kg
```

## What it optimizes

A shopping list is `{product: number_of_packs}`. Three problems, increasing in
difficulty:

**1. Single-store optimum.** Total each store's basket (flagging items a store
doesn't carry) and rank cheapest-first. A fully-stocked store is preferred over a
cheaper-but-incomplete one. → `single_store_totals`, `best_single_store`.

**2. Per-item-cheapest split (unconstrained).** Buy each item wherever it's
cheapest, ignoring how many stores that implies. This is a true *lower bound* on
item cost — but visiting every store is rarely practical, so it's the optimistic
benchmark, not a real plan. → `per_item_cheapest`.

**3. Constrained ≤k-store split (the real optimization).** Buy the whole list
visiting **at most `k` stores**, paying a fixed **`visit_cost` per store
visited**. This trades item savings against trips. Solved *exactly* by
enumerating store subsets of size ≤ k: for a fixed set of stores, each item goes
to the cheapest store in the set that carries it, so scoring a subset is trivial
and we keep the best subset. A separate `brute_force_split` (every item→store
assignment) is used by the tests to prove the subset method returns the true
optimum. → `best_constrained_split`.

### Why the trip cost matters

Without a trip cost, the answer is always "buy each item at its cheapest store" —
not interesting. The `visit_cost` turns it into a genuine trade-off: an extra
store only earns its place if the items you'd buy there save more than the trip
costs. Below, the unconstrained split has the lowest *item* cost but loses on
*all-in* cost because it needs three trips.

## Unit-price normalization

Pack sizes are normalized to a base unit (kg / litre / each) so a cheaper sticker
price can still be the worse deal. From the committed catalog:

| Store | Olive Oil pack | Price | Unit price |
|---|---|---:|---:|
| GreenBasket | 1 L | EUR 6.20 | 6.20 /L |
| MartMax | 750 ml | EUR 5.90 | 7.87 /L |
| **ValuMart** | **2 L** | **EUR 9.60** | **4.80 /L** ✅ |

ValuMart's bottle has the **highest** sticker price but the **lowest** price per
litre, so `best_unit_value("Olive Oil")` correctly picks it.

## Worked example (real output of `demo.py`)

Catalog: 4 stores, 20 products, 75 offers. Trip cost: **EUR 1.00 per store**.
Shopping list: Milk ×2, Bread, Eggs, Bananas, Coffee, Chicken, Pasta ×2, Cheese,
Orange Juice, Yogurt.

| Strategy | Stores | Item cost | Trips | **All-in** |
|---|---|---:|---:|---:|
| Best single store (GreenBasket) | 1 | 25.60 | 1.00 | **26.60** |
| Per-item-cheapest split | 3 | **23.55** | 3.00 | 26.55 |
| **Best ≤2-store plan (GreenBasket + MartMax)** | 2 | 23.90 | 2.00 | **25.90** ✅ |

The unconstrained split has the lowest item cost (23.55) but three trips push its
all-in cost to 26.55. The **≤2-store plan wins at EUR 25.90 all-in — EUR 0.70
(2.6%) cheaper than the best single store**, by sending Bread/Bananas/Coffee/
Pasta/Orange Juice to GreenBasket and Milk/Eggs/Chicken/Cheese/Yogurt to MartMax.

```
python demo.py
```

## Install & run

```bash
pip install -r requirements.txt
python demo.py            # worked example above
python -m pytest -q       # 13 tests
```

```python
from shopsmart import (
    demo_catalog, sample_shopping_list,
    best_single_store, per_item_cheapest, best_constrained_split,
)
cat, sl = demo_catalog(), sample_shopping_list()
best_single_store(cat, sl).store                         # 'GreenBasket'
best_constrained_split(cat, sl, max_stores=2, visit_cost=1.0).total   # 25.90
```

## Tests

`tests/test_optimizer.py` checks each property against hand-computed answers and
cross-checks the optimizer against brute force:

- single-store ranking matches a hand-totalled price table;
- per-item-cheapest split equals the known minimum and is a proven lower bound;
- the ≤k-store optimizer equals brute force on small instances, including a
  60-instance randomized comparison across store counts and trip costs;
- a high trip cost correctly collapses the plan to one store;
- unit-price normalization picks the better value across pack sizes (mass *and*
  volume units);
- missing items are flagged, not crashed on, and an unfulfillable list raises.

```
13 passed
```

## Layout

```
shopsmart/
  catalog.py     Offer + Catalog, unit-price normalization
  optimizer.py   single-store, per-item split, ≤k-store optimizer, brute force
  data.py        committed synthetic catalog + sample list
demo.py          worked example
tests/           pytest suite
index.html       static showcase site
```

Catalog data is synthetic and for demonstration only.
