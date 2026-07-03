import os
import pyodbc
import json

# Global configuration dictionary
db_config = {
    "server": "localhost",
    "database": "CampusBite",
    "trusted": True,
    "username": "",
    "password": "",
}

def set_connection_config(server: str, database: str, trusted: bool, username: str = "", password: str = ""):
    db_config["server"] = server
    db_config["database"] = database
    db_config["trusted"] = trusted
    db_config["username"] = username
    db_config["password"] = password

def get_connection():
    try:
        if db_config["trusted"]:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={db_config['server']};"
                f"DATABASE={db_config['database']};"
                f"Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={db_config['server']};"
                f"DATABASE={db_config['database']};"
                f"UID={db_config['username']};"
                f"PWD={db_config['password']};"
            )
        conn = pyodbc.connect(conn_str)
        # print("Connected successfully to SQL Server!")
        return conn
    except pyodbc.Error as e:
        print("Connection failed. Let's find out why:")
        print(e)
        raise e

def get_live_schema():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
         SELECT
            TABLE_NAME,
            COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_NAME
    """)

    schema = {}

    for row in cursor.fetchall():
        table = row.TABLE_NAME
        column = row.COLUMN_NAME

        if table not in schema:
            schema[table] = []

        schema[table].append(column)
    conn.close()
    return schema

def create_database_from_schema():
    """
    Reads the schema.json file and creates the corresponding tables in the database.
    This is an idempotent operation; it won't fail if tables already exist.
    """
    try:
        with open('MCP/SQLMCP/schema.json', 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print("schema.json not found!")
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Basic type inference from column names
    def infer_type(column_name):
        name = column_name.lower()
        if name.endswith('_id'):
            return "INT"
        if name.endswith('_date'):
            return "DATETIME"
        if 'email' in name:
            return "NVARCHAR(255)"
        if 'name' in name or 'description' in name or 'status' in name or 'city' in name or 'state' in name:
            return "NVARCHAR(255)"
        if 'score' in name or 'salary' in name or 'latitude' in name or 'longitude' in name:
            return "DECIMAL(18, 5)"
        return "NVARCHAR(MAX)"

    # Create tables without constraints first
    for table_name, columns in schema.items():
        sql = f"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' and xtype='U') CREATE TABLE {table_name} ("
        column_defs = []
        for column_name in columns:
            col_type = infer_type(column_name)
            if column_name.lower().endswith('_id') and not any(fk_col in column_name.lower() for fk_col in ['company', 'site', 'auditor', 'audit', 'worker']):
                 column_defs.append(f"{column_name} {col_type} PRIMARY KEY")
            else:
                 column_defs.append(f"{column_name} {col_type}")
        sql += ", ".join(column_defs)
        sql += ");"
        try:
            cursor.execute(sql)
        except pyodbc.Error as e:
            print(f"Error creating table {table_name}: {e}")
            # This might fail if run out of order, but we'll add FKs next

    # Add foreign key constraints
    fk_constraints = {
        'sites': 'FOREIGN KEY (company_id) REFERENCES companies(company_id)',
        'workers': 'FOREIGN KEY (site_id) REFERENCES sites(site_id)',
        'audits': ['FOREIGN KEY (auditor_id) REFERENCES auditors(auditor_id)', 'FOREIGN KEY (site_id) REFERENCES sites(site_id)'],
        'audit_findings': 'FOREIGN KEY (audit_id) REFERENCES audits(audit_id)',
        'worker_attendance': 'FOREIGN KEY (worker_id) REFERENCES workers(worker_id)',
        'equipment': 'FOREIGN KEY (site_id) REFERENCES sites(site_id)'
    }

    for table, constraints in fk_constraints.items():
        if isinstance(constraints, list):
            for constraint in constraints:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD {constraint};")
                except pyodbc.Error as e:
                    print(f"Warning: Could not add FK '{constraint}' to table {table}. It might already exist. Error: {e}")
        else:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD {constraints};")
            except pyodbc.Error as e:
                print(f"Warning: Could not add FK '{constraints}' to table {table}. It might already exist. Error: {e}")


    conn.commit()
    conn.close()
    print("Database schema created/verified successfully.")