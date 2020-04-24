mime_types = {
    'csv': 'text/csv; q=1.0, */*; q=0.1',
    'json': 'application/json; q=1.0, application/sparql-results+json; q=0.8, */*; q=0.1',
    'html': 'text/html; q=1.0, */*; q=0.1',
    'ttl': 'text/turtle'
}
GET_ALL_QUERY = "get_all"
GET_ALL_RELATED_QUERY = "get_all_related"
GET_ALL_RELATED_USER_QUERY = "get_all_related_user"
GET_ALL_USER_QUERY = "get_all_user"
GET_ONE_QUERY = "get_one"
GET_ONE_USER_QUERY = "get_one_user"

XSD_DATATYPES = ["decimal", "float", "double", "integer", "positiveInteger", "negativeInteger", "nonPositiveInteger", "nonNegativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte", "dateTime", "date", "gYearMonth", "gYear", "duration", "gMonthDay", "gDay", "gMonth", "string", "normalizedString", "token", "language", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID", "IDREFS", "ENTITY", "ENTITIES", "QName", "boolean", "hexBinary", "base64Binary", "anyURI", "notation"]
