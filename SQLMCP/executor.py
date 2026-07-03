from sqlglot import parse_one, exp

from database import get_connection
from history import record_query_history


def _expression_type(name: str):
    return getattr(exp, name, None)


def classify_query(sql: str) -> str:
    try:
        tree = parse_one(sql)
    except Exception:
        return "UNKNOWN"

    select_type = _expression_type("Select")
    insert_type = _expression_type("Insert")
    update_type = _expression_type("Update")
    delete_type = _expression_type("Delete")
    alter_type = _expression_type("Alter")
    drop_type = _expression_type("Drop")
    create_type = _expression_type("Create")
    truncate_type = _expression_type("Truncate")

    if select_type and isinstance(tree, select_type):
        return "READ"

    if (insert_type and isinstance(tree, insert_type)) or (update_type and isinstance(tree, update_type)):
        return "WRITE"

    if (
        (delete_type and isinstance(tree, delete_type))
        or (alter_type and isinstance(tree, alter_type))
        or (drop_type and isinstance(tree, drop_type))
        or (create_type and isinstance(tree, create_type))
        or (truncate_type and isinstance(tree, truncate_type))
    ):
        return "ADMIN"

    return "OTHER"


def explain_query(sql: str):
    try:
        tree = parse_one(sql)
    except Exception as exc:
        return {
            "success": False,
            "error": f"Unable to parse SQL: {exc}",
        }

    tables = sorted({table.name for table in tree.find_all(exp.Table)})
    columns = sorted({column.name for column in tree.find_all(exp.Column)})
    query_type = classify_query(sql)

    purpose = ""
    if query_type == "READ":
        purpose = "Retrieve data from the referenced tables."
    elif query_type == "WRITE":
        purpose = "Modify existing rows or insert new rows."
    elif query_type == "ADMIN":
        purpose = "Perform schema or destructive database operations."
    else:
        purpose = "Execute a SQL statement that does not fit the main read/write/admin categories."

    return {
        "success": True,
        "query_type": query_type,
        "tables": tables,
        "columns": columns,
        "purpose": purpose,
    }


def execute_select(sql: str):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(sql)

        columns = [column[0] for column in cursor.description]
        results = []

        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        result = {
            "success": True,
            "query_type": "READ",
            "data": results,
        }
        return result
    finally:
        connection.close()


def execute_write(sql: str, approved: bool = False):
    if not approved:
        return {
            "success": False,
            "query_type": "WRITE",
            "error": "Write queries require explicit approval before execution.",
        }

    query_type = classify_query(sql)
    if query_type != "WRITE":
        return {
            "success": False,
            "query_type": query_type,
            "error": "Only INSERT and UPDATE queries are allowed in the write executor.",
        }

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(sql)
        connection.commit()

        result = {
            "success": True,
            "query_type": "WRITE",
            "rows_affected": cursor.rowcount,
        }
        return result
    finally:
        connection.close()


def execute_sql(sql: str, approved: bool = False):
    query_type = classify_query(sql)

    if query_type == "READ":
        result = execute_select(sql)
        return result

    if query_type == "WRITE":
        result = execute_write(sql, approved=approved)
        return result

    return {
        "success": False,
        "query_type": query_type,
        "error": "Only SELECT, INSERT, and UPDATE queries are supported for execution.",
    }


def run_and_record_query(question: str, sql: str, validation: dict, approved: bool = False):
    query_type = classify_query(sql)

    if validation.get("valid") is not True:
        execution_result = {
            "success": False,
            "error": "SQL validation failed.",
        }
        record_query_history(question, sql, query_type, validation, execution_result, approved=approved)
        return execution_result

    execution_result = execute_sql(sql, approved=approved)
    record_query_history(question, sql, query_type, validation, execution_result, approved=approved)
    return execution_result