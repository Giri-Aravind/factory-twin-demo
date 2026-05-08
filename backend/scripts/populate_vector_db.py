"""Load endpoints into Qdrant.

Catalog (schema/endpoint_catalog.py) is the single source of truth for
vector-DB-time information:
  - ENDPOINT_SELECTION_TEXT: the text that gets embedded
  - ENDPOINT_CATEGORIES:     which bucket each endpoint belongs to

Schema (schema/endpoint_schema.py) owns GraphQL execution details only
(query strings, variables, response paths). It is imported here ONLY for
a consistency check — every endpoint name in the catalog must exist in
the schema, and vice versa, so a missing catalog entry or schema entry
fails loudly at populate time instead of silently at query time.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__) + "/..")

from scripts.vectordb import vectordb
from schema.endpoint_catalog import ENDPOINT_SELECTION_TEXT, ENDPOINT_CATEGORIES
from schema.endpoint_schema import ENDPOINT_NAMES


def _check_consistency() -> None:
    catalog_text_names = set(ENDPOINT_SELECTION_TEXT.keys())
    catalog_cat_names = set(ENDPOINT_CATEGORIES.keys())
    schema_names = set(ENDPOINT_NAMES)

    # Catalog internally consistent
    text_only = catalog_text_names - catalog_cat_names
    cat_only = catalog_cat_names - catalog_text_names
    if text_only:
        raise ValueError(
            f"In ENDPOINT_SELECTION_TEXT but missing from ENDPOINT_CATEGORIES: {text_only}"
        )
    if cat_only:
        raise ValueError(
            f"In ENDPOINT_CATEGORIES but missing from ENDPOINT_SELECTION_TEXT: {cat_only}"
        )

    # Catalog and schema agree on names
    missing_in_catalog = schema_names - catalog_text_names
    missing_in_schema = catalog_text_names - schema_names
    if missing_in_catalog:
        raise ValueError(
            f"In endpoint_schema.py but missing from endpoint_catalog.py: {missing_in_catalog}"
        )
    if missing_in_schema:
        raise ValueError(
            f"In endpoint_catalog.py but missing from endpoint_schema.py: {missing_in_schema}"
        )


def populate():
    print("\n" + "=" * 50)
    print("Populating Vector DB")
    print("=" * 50)

    _check_consistency()
    print(f"Consistency check OK ({len(ENDPOINT_SELECTION_TEXT)} endpoints).\n")

    vectordb.initialize()
    print("Collection created.\n")

    for endpoint_name, selection_text in ENDPOINT_SELECTION_TEXT.items():
        category = ENDPOINT_CATEGORIES[endpoint_name]
        vectordb.add_endpoint(endpoint_name, selection_text, category)
        print(f"  + {endpoint_name} [{category}]")

    print(f"\nDone — {len(ENDPOINT_SELECTION_TEXT)} endpoints loaded.\n")

    # Quick sanity probe
    tests = [
        ("Show me total aggregate demand", "Demand Planning"),
        ("Monthly demand by customer", "Demand Planning"),
        ("Material shortage for Titanium Bolt", "Supply Planning"),
        ("What purchase orders should I place?", "Supply Planning"),
        ("Break down OSP demand by customer", "Supply Planning"),
    ]
    print("Sanity probes:")
    for q, expected_cat in tests:
        results = vectordb.search(q, limit=1)
        if results:
            r = results[0]
            ok = "OK" if r["category"] == expected_cat else "??"
            print(f"  [{ok}] '{q}' -> {r['endpoint_name']} ({r['category']}, {r['score']})")


if __name__ == "__main__":
    populate()