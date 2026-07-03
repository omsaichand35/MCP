from sqlglot import parse_one, exp
from database import get_live_schema


def extract_tables(sql: str):
    tree = parse_one(sql)

    return [
        table.name
        for table in tree.find_all(exp.Table)
    ]


def extract_columns(sql: str):
    tree = parse_one(sql)

    columns = []

    for column in tree.find_all(exp.Column):
        columns.append(
            {
                "table_alias": column.table,
                "column_name": column.name
            }
        )

    return columns


def extract_alias_mapping(sql: str):
    tree = parse_one(sql)

    mapping = {}

    for table in tree.find_all(exp.Table):

        if table.alias:
            mapping[table.alias] = table.name

    return mapping


def validate_tables(sql: str):
    schema = get_live_schema()

    existing_tables = set(schema.keys())

    tables = extract_tables(sql)

    errors = []

    for table in tables:

        if table not in existing_tables:

            errors.append(
                f"Table '{table}' does not exist"
            )

    return errors


def validate_columns(sql: str):
    schema = get_live_schema()

    alias_mapping = extract_alias_mapping(sql)

    columns = extract_columns(sql)

    errors = []

    for column in columns:

        alias = column["table_alias"]
        column_name = column["column_name"]

        if not alias:
            continue

        if alias not in alias_mapping:
            continue

        table_name = alias_mapping[alias]

        if column_name not in schema[table_name]:

            errors.append(
                f"Column '{column_name}' does not exist in table '{table_name}'"
            )

    return errors


def validate_sql(sql: str):

    errors = []

    errors.extend(validate_tables(sql))
    errors.extend(validate_columns(sql))

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }