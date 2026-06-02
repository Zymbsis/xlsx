MAP_COLUMNS_SYSTEM_PROMPT = """\
You identify columns in a spreadsheet preview.

Find two columns by 0-based index:
    - domain_column: values that look like a domain (host.tld),
    regardless of whether the TLD is real (e.g. "acme.com", "0wmcrj.bpt")
    - company_name_column: company / organization names.
    Names may be short or contain digits (e.g. "Acme Inc.", "1045", "10up", "NYC Dental").

Rules:
    - If a column is not present, return null. Do not guess.
    - "has_header" is true if the first row contains text labels describing the columns
    (any of them, not necessarily just the two you identified).
    - Return ONLY valid JSON matching this schema:
        {"company_name_column": <int | null>, "domain_column": <int | null>, "has_header": <bool>}
"""

MAP_COLUMNS_USER_TEMPLATE = """\
Spreadsheet preview ({n_rows} rows x {n_cols} cols):

{preview}\
"""
