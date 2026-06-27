"""ShopSmart demo: cheapest single store vs. unconstrained split vs. best ≤2-store plan.

Run:  python demo.py
"""

from __future__ import annotations

from shopsmart import (
    best_constrained_split,
    best_single_store,
    demo_catalog,
    per_item_cheapest,
    sample_shopping_list,
    single_store_totals,
)

VISIT_COST = 1.00  # modelled cost of an extra supermarket trip (EUR)


def money(x: float) -> str:
    return f"EUR {x:6.2f}"


def main() -> None:
    cat = demo_catalog()
    sl = sample_shopping_list()

    print("=" * 64)
    print("ShopSmart - basket optimization (synthetic catalog)")
    print("=" * 64)
    print(f"Stores:   {', '.join(cat.stores)}")
    print(f"Catalog:  {len(cat.products)} products, {len(cat.offers)} offers")
    print("\nShopping list (product x packs):")
    for p, q in sl.items():
        print(f"  - {p:<14} x{int(q)}")

    # --- 1. single-store ranking -------------------------------------------
    print("\n" + "-" * 64)
    print("1) Cheapest SINGLE store (one trip, whole basket)")
    print("-" * 64)
    ranked = single_store_totals(cat, sl)
    for r in ranked:
        flag = "" if r.complete else f"  (missing: {', '.join(r.missing)})"
        print(f"  {r.store:<12} {money(r.total)}{flag}")
    best_store = best_single_store(cat, sl)
    print(f"\n  -> Best single store: {best_store.store} at {money(best_store.total)}")

    # --- 2. unconstrained per-item-cheapest split --------------------------
    print("\n" + "-" * 64)
    print("2) Per-item CHEAPEST split (buy each item at its cheapest store)")
    print("-" * 64)
    split = per_item_cheapest(cat, sl, visit_cost=VISIT_COST)
    for p, store in split.assignment.items():
        print(f"  {p:<14} -> {store:<12} {money(cat.price(store, p) * sl[p])}")
    print(f"\n  Item cost:           {money(split.item_cost)}")
    print(f"  Stores visited:      {split.num_stores}  ({', '.join(split.stores_used)})")
    print(f"  + trip cost @ {money(VISIT_COST)}/store = {money(split.visit_cost)}")
    print(f"  -> All-in total:     {money(split.total)}")

    # --- 3. best constrained <=2-store plan --------------------------------
    print("\n" + "-" * 64)
    print(f"3) Best <=2-store plan (trip cost {money(VISIT_COST)} per store)")
    print("-" * 64)
    plan = best_constrained_split(cat, sl, max_stores=2, visit_cost=VISIT_COST)
    for store in plan.stores_used:
        items = [p for p, s in plan.assignment.items() if s == store]
        sub = sum(cat.price(store, p) * sl[p] for p in items)
        print(f"  {store:<12} {money(sub)}  <- {', '.join(items)}")
    print(f"\n  Item cost:           {money(plan.item_cost)}")
    print(f"  Stores visited:      {plan.num_stores}  ({', '.join(plan.stores_used)})")
    print(f"  + trip cost:         {money(plan.visit_cost)}")
    print(f"  -> All-in total:     {money(plan.total)}")

    # --- summary ------------------------------------------------------------
    print("\n" + "=" * 64)
    print("SUMMARY (all-in, including trip cost where applicable)")
    print("=" * 64)
    one_trip = best_store.total + VISIT_COST  # one store = one trip
    print(f"  Single store ({best_store.store}), 1 trip:   {money(one_trip)}")
    print(f"  Best <=2-store plan:            {money(plan.total)}")
    print(f"  Unconstrained split ({split.num_stores} stores):  {money(split.total)}")

    save_vs_single = one_trip - plan.total
    print(
        f"\n  The 2-store plan saves {money(save_vs_single)} vs. the best single store"
        f" ({save_vs_single / one_trip * 100:.1f}%)."
    )
    item_only_save = best_store.total - split.item_cost
    print(
        f"  Buying every item at its cheapest store would cut item cost by "
        f"{money(item_only_save)}, but needs {split.num_stores} trips - "
        f"the trip cost makes that {'worse' if split.total > plan.total else 'better'}."
    )


if __name__ == "__main__":
    main()
