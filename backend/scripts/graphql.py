"""Execute GraphQL queries against the FactoryTwin backend."""
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()


_OPERATION_NAME_RE = re.compile(r"^\s*query\s+([A-Za-z_][A-Za-z0-9_]*)")


def _extract_operation_name(query: str) -> str:
    """Pull the operation name out of a GraphQL query string.

    For 'query DemandByCategory(...)' returns 'DemandByCategory'.
    Returns an empty string if the query is anonymous (some servers tolerate
    this when there's only one operation in the document).
    """
    if not query:
        return ""
    m = _OPERATION_NAME_RE.match(query)
    return m.group(1) if m else ""


class GraphQL:
    def __init__(self):
        self.url = os.getenv(
            "FACTORYTWIN_GRAPHQL_URL", "http://10.1.10.184:9000/graphql"
        )
        self.timeout = 120

    def execute(self, query: str, variables: dict, operation_name: str | None = None):
        """POST {operationName, query, variables} to the GraphQL endpoint.

        operation_name is auto-extracted from the query if not provided.
        """
        if operation_name is None:
            operation_name = _extract_operation_name(query)

        # Drop None-valued variables. Optional vars (UUID without `!`) accept
        # null at the schema level, but some Hot Chocolate / Graphene servers
        # are picky about Instant/Boolean nulls. Sending only the keys we
        # actually filled is the safe default.
        clean_vars = {k: v for k, v in (variables or {}).items() if v is not None}

        body = {
            "operationName": operation_name,
            "query": query,
            "variables": clean_vars,
        }

        try:
            resp = requests.post(
                self.url,
                json=body,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to FactoryTwin at {self.url}. Check VPN."
            )
        except requests.Timeout:
            raise TimeoutError(f"GraphQL timed out after {self.timeout}s.")

        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")

        result = resp.json()
        if "errors" in result:
            first_err = result["errors"][0].get("message", "Unknown")
            raise Exception(f"GraphQL error: {first_err}")

        return result.get("data", result)

    @staticmethod
    def extract_data(result, path):
        """Walk a nested response by path. Returns None if a key is missing."""
        data = result
        for key in path or []:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data


graphql = GraphQL()