"""PostgreSQL connector — resolves names to UUIDs against the
temporalfactory schema.

All operational tables follow the temporal-versioning + multi-tenant pattern:
  - rowdeath IS NULL            (current row)
  - division = :division        (tenant scope)
  - lower(name) = lower(:value) (case-insensitive exact match)

If exact match yields nothing, fall back to a substring LIKE.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


# Tables the SQL agent is allowed to look up against. Keeps the agent from
# being tricked into querying arbitrary tables if the LLM hallucinates
# something off-spec.
ALLOWED_LOOKUP_TABLES = {"site", "part", "companysite", "process"}


class Postgres:
    def __init__(self):
        self.engine = None

    def _get_engine(self):
        if self.engine is None:
            url = (
                f"postgresql://{os.getenv('FACTORYTWIN_DB_USER', 'postgres')}:"
                f"{os.getenv('FACTORYTWIN_DB_PASSWORD', '')}@"
                f"{os.getenv('FACTORYTWIN_DB_HOST', 'localhost')}:"
                f"{os.getenv('FACTORYTWIN_DB_PORT', '5432')}/"
                f"{os.getenv('FACTORYTWIN_DB_NAME', 'factorytwin')}"
            )
            self.engine = create_engine(url, pool_pre_ping=True)
        return self.engine

    def _division(self):
        div = os.getenv("FACTORYTWIN_DIVISION_UUID")
        if not div:
            raise RuntimeError(
                "FACTORYTWIN_DIVISION_UUID not set. Cannot run multi-tenant "
                "queries without a division UUID."
            )
        return div

    def _resolve_one(self, table: str, name: str) -> str | None:
        """Resolve a single name to a single UUID for the given table.

        Strategy:
          1. case-insensitive exact match on `name` column
          2. fallback to substring LIKE on `name` column (warns if multiple
             rows match — returns the first by `name` ordering)
        """
        if table not in ALLOWED_LOOKUP_TABLES:
            raise ValueError(f"Lookup against table '{table}' is not allowed.")

        division = self._division()
        engine = self._get_engine()

        with engine.connect() as conn:
            # 1) exact match
            row = conn.execute(
                text(
                    f"""
                    SELECT identifier
                    FROM temporalfactory.{table}
                    WHERE division = :division
                      AND rowdeath IS NULL
                      AND lower(name) = lower(:name)
                    ORDER BY name
                    LIMIT 2
                    """
                ),
                {"division": division, "name": name},
            ).fetchall()

            if len(row) == 1:
                return str(row[0][0])
            if len(row) >= 2:
                print(
                    f"  [Postgres] Ambiguous: '{name}' matches multiple rows "
                    f"in {table} (division={division[:8]}...). "
                    f"Using first by name order."
                )
                return str(row[0][0])

            # 2) substring fallback
            row = conn.execute(
                text(
                    f"""
                    SELECT identifier, name
                    FROM temporalfactory.{table}
                    WHERE division = :division
                      AND rowdeath IS NULL
                      AND lower(name) LIKE lower(:pattern)
                    ORDER BY name
                    LIMIT 5
                    """
                ),
                {"division": division, "pattern": f"%{name}%"},
            ).fetchall()

            if not row:
                print(f"  [Postgres] '{name}' not found in {table}.")
                return None
            if len(row) > 1:
                names = ", ".join(r[1] for r in row[:3])
                print(
                    f"  [Postgres] Substring '{name}' matched multiple in "
                    f"{table}: {names}. Using first."
                )
            return str(row[0][0])

    def resolve_lookup(
        self,
        table: str,
        lookup_value,
        return_as: str,
    ):
        """Resolve a list of names (or single name) to UUIDs.

        lookup_value: list[str] or str
        return_as:    "list" or "single"

        Returns:
            list[str]  if return_as == "list"
            str | None if return_as == "single"
        """
        # Normalize input to a list
        if isinstance(lookup_value, str):
            names = [lookup_value]
        elif isinstance(lookup_value, list):
            names = [str(n) for n in lookup_value if n]
        else:
            names = []

        if return_as not in ("list", "single"):
            raise ValueError(f"return_as must be 'list' or 'single', got {return_as!r}")

        # Special case: empty list for sites means "all sites"
        if not names:
            if return_as == "list":
                return []
            return None

        uuids = []
        for nm in names:
            uid = self._resolve_one(table, nm)
            if uid:
                uuids.append(uid)

        if return_as == "list":
            return uuids

        # return_as == "single"
        return uuids[0] if uuids else None

    def verify_connection(self):
        """Ping check used by setup_db.py / health endpoints."""
        try:
            with self._get_engine().connect() as conn:
                r = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM temporalfactory.site "
                        "WHERE rowdeath IS NULL AND division = :division"
                    ),
                    {"division": self._division()},
                )
                count = r.fetchone()[0]
                return True, count
        except Exception as e:
            return False, str(e)


postgres = Postgres()