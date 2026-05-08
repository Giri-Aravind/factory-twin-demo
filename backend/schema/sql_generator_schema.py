sql_generator_system_prompt = """
This agent does not use an LLM. It resolves names to UUIDs via PostgreSQL
and builds the final GraphQL variables dict.

Logic:
1. Start with ALL defaults from the endpoint schema
2. Override sites with resolved UUIDs (if user specified)
3. Override selectedMaterial/part/partSupplier with resolved UUIDs (if user specified)
4. Override stackType (if user specified)
5. Override from/until (if user specified a time period)
6. Set simulation UUID from settings

No LLM call needed - pure Python + PostgreSQL.
"""
