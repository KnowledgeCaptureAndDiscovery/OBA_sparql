mime_types = {
    'csv': 'text/csv; q=1.0, */*; q=0.1',
    'json': 'application/json; q=1.0, application/sparql-results+json; q=0.8, */*; q=0.1',
    'html': 'text/html; q=1.0, */*; q=0.1',
    'ttl': 'text/turtle'
}
QUERY_TYPE_GET_ALL = "get_all"
QUERY_TYPE_GET_ALL_USER = "get_all_user"
QUERY_TYPE_GET_ONE = "get_one"
QUERY_TYPE_GET_ONE_USER = "get_one_user"
QUERIES_TYPES = [QUERY_TYPE_GET_ALL, QUERY_TYPE_GET_ALL_USER, QUERY_TYPE_GET_ONE, QUERY_TYPE_GET_ONE_USER]

XSD_DATATYPES = ["decimal", "float", "double", "integer", "positiveInteger", "negativeInteger", "nonPositiveInteger",
                 "nonNegativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort",
                 "unsignedByte", "dateTime", "date", "gYearMonth", "gYear", "duration", "gMonthDay", "gDay", "gMonth",
                 "string", "normalizedString", "token", "language", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID",
                 "IDREFS", "ENTITY", "ENTITIES", "QName", "boolean", "hexBinary", "base64Binary", "anyURI", "notation"]
