def init(**kwargs):
    """Initialize OBA Sparql API Client.
    Keyword Args:
        queries_dir (str): Directory of queries.
        context_dir (str): Directory of context.
        queries_types (array): Queries types enabled.
    """
    _creds = _load_creds(**kwargs)
    return ApiClient(**_creds)