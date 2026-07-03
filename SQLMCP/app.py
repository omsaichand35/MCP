import streamlit as st
import pandas as pd
import json

from database import set_connection_config, get_connection, get_live_schema, create_database_from_schema
from executor import classify_query, explain_query, run_and_record_query
from ollama_client import generate_sql, generate_schema_from_prompt
from validator import validate_sql
from history import get_query_history

st.set_page_config(page_title="AI Database Copilot", page_icon="🤖", layout="wide")

# --- Session State Initialization ---
if "connected" not in st.session_state:
    st.session_state.connected = False
if "schema" not in st.session_state:
    st.session_state.schema = None
if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None
if "current_response" not in st.session_state:
    st.session_state.current_response = None

# --- Sidebar: History & Config ---
with st.sidebar:
    st.title("⚙️ Configuration")
    if not st.session_state.connected:
        st.subheader("Database Connection")
        server = st.text_input("Server Name", value="localhost")
        database = st.text_input("Database Name", value="CampusBite")
        auth_type = st.selectbox("Authentication", ["Windows Authentication", "SQL Server Authentication"])
        
        user, pwd = "", ""
        if auth_type == "SQL Server Authentication":
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            
        if st.button("Connect"):
            trusted = auth_type == "Windows Authentication"
            set_connection_config(server, database, trusted, user, pwd)
            try:
                # Create and verify the database schema
                create_database_from_schema()
                
                # Test connection and cache schema
                conn = get_connection()
                st.session_state.schema = get_live_schema()
                st.session_state.connected = True
                st.success("✓ Connected and schema verified!")
                st.rerun()
            except Exception as e:
                st.error(f"Connection Failed: {e}")
    else:
        st.success("Connected to Database")
        if st.button("Disconnect"):
            st.session_state.connected = False
            st.session_state.schema = None
            st.session_state.pending_approval = None
            st.session_state.current_response = None
            st.rerun()
            
    st.divider()
    st.title("📜 Query History")
    if st.session_state.connected:
        history = get_query_history(10)
        for h in history:
            with st.expander(f"{h['query_type']} - {h['created_at'][:16]}"):
                st.write(f"**Q:** {h['question']}")
                st.code(h['sql'], language="sql")
                st.write("Status: ", "✅ Approved/Ran" if h['approved'] else "❌ Not Approved/Failed")

# --- Main App ---
st.title("🤖 AI Database Copilot")

# --- Schema Definition Mode ---
schema_mode = st.radio(
    "How do you want to define the schema?",
    ('Use existing schema from `schema.json`', 'Generate schema from a new prompt')
)

if schema_mode == 'Generate schema from a new prompt':
    schema_prompt = st.text_area("Describe your database schema:", height=200, placeholder="e.g., A table for companies with id and name, and a table for sites with id, company_id, and location...")
    if st.button("Generate and Build Schema"):
        if schema_prompt:
            with st.spinner("🧠 Generating schema from your description..."):
                new_schema = generate_schema_from_prompt(schema_prompt)
                if new_schema:
                    # Overwrite schema.json with the new schema
                    with open('MCP/SQLMCP/schema.json', 'w') as f:
                        json.dump(new_schema, f, indent=2)
                    st.success("✅ New schema generated and saved!")
                    
                    # Attempt to build this schema in the database
                    with st.spinner("🏗️ Building database tables..."):
                        try:
                            create_database_from_schema()
                            st.success("✅ Database tables created/updated successfully!")
                            # Refresh the live schema view
                            st.session_state.schema = get_live_schema()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to build database tables: {e}")
                else:
                    st.error("Could not generate a valid schema from the prompt. Please try rephrasing.")
        else:
            st.warning("Please enter a schema description.")

if not st.session_state.connected:
    st.info("Please connect to a SQL Server database using the sidebar.")
    st.stop()

# Show Schema Overview
with st.expander("📊 Database Schema Overview"):
    schema = st.session_state.schema
    if schema:
        cols = st.columns(3)
        for i, (table, columns) in enumerate(schema.items()):
            with cols[i % 3]:
                st.markdown(f"**{table}**")
                st.caption(", ".join(columns))

st.divider()

# --- NL Query Input ---
question = st.text_area("Ask a question about your data:", placeholder="E.g., Show all students from A Block")

if st.button("Generate & Run SQL", type="primary"):
    if question:
        with st.spinner("Generating SQL..."):
            retries = 3
            current_question = question
            sql = ""
            validation = {"valid": False}
            
            for attempt in range(retries):
                sql = generate_sql(current_question)
                validation = validate_sql(sql)
                if validation["valid"]:
                    break
                else:
                    errors = ", ".join(validation["errors"])
                    current_question = f"Previous query failed validation with errors: {errors}. Please fix the SQL for: {question}"

            query_type = classify_query(sql)
            explanation = explain_query(sql)
            
            st.session_state.current_response = {
                "question": question,
                "sql": sql,
                "validation": validation,
                "query_type": query_type,
                "explanation": explanation
            }
            
            if not validation["valid"]:
                st.session_state.current_response["result"] = run_and_record_query(question, sql, validation, False)
                st.session_state.pending_approval = None
            elif query_type in ["WRITE", "ADMIN"]:
                st.session_state.pending_approval = True
            else:
                # READ queries execute immediately
                st.session_state.current_response["result"] = run_and_record_query(question, sql, validation, True)
                st.session_state.pending_approval = None
                
# --- Output Display ---
if st.session_state.current_response:
    resp = st.session_state.current_response
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Generated SQL")
        st.code(resp["sql"], language="sql")
        
        st.subheader("Query Classification")
        if resp["query_type"] == "READ":
            st.info("READ (SELECT) - Executes Automatically")
        elif resp["query_type"] == "WRITE":
            st.warning("WRITE (INSERT/UPDATE) - Requires Approval")
        elif resp["query_type"] == "ADMIN":
            st.error("ADMIN (DROP/ALTER) - Requires Approval")
        else:
            st.error("UNKNOWN TYPE")
            
    with col2:
        st.subheader("Validation Status")
        if resp["validation"]["valid"]:
            st.success("✓ PASS: Tables and columns are valid.")
        else:
            st.error("✗ FAIL")
            for err in resp["validation"]["errors"]:
                st.write(f"- {err}")
                
        with st.expander("Query Explanation"):
            if resp["explanation"].get("success"):
                st.write("**Purpose:**", resp["explanation"]["purpose"])
                st.write("**Tables:**", ", ".join(resp["explanation"]["tables"]))
                st.write("**Columns:**", ", ".join(resp["explanation"]["columns"]))
            else:
                st.write("Could not generate explanation.")

    st.divider()
    
    # --- Approval Workflow ---
    if st.session_state.pending_approval:
        st.warning("⚠️ This query modifies data or schema. Do you approve execution?")
        c1, c2 = st.columns([1, 10])
        with c1:
            if st.button("✅ Approve"):
                with st.spinner("Executing..."):
                    res = run_and_record_query(resp["question"], resp["sql"], resp["validation"], True)
                    st.session_state.current_response["result"] = res
                    st.session_state.pending_approval = False
                    st.rerun()
        with c2:
            if st.button("❌ Reject"):
                with st.spinner("Recording rejection..."):
                    res = run_and_record_query(resp["question"], resp["sql"], resp["validation"], False)
                    res["error"] = "User rejected the query."
                    st.session_state.current_response["result"] = res
                    st.session_state.pending_approval = False
                    st.rerun()

    # --- Results Viewer ---
    if "result" in resp:
        res = resp["result"]
        st.subheader("Results")
        if res.get("success"):
            if resp["query_type"] == "READ":
                data = res.get("data", [])
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", csv, "results.csv", "text/csv")
                else:
                    st.info("Query executed successfully, but returned 0 rows.")
            else:
                st.success(f"Query executed successfully. Rows affected: {res.get('rows_affected', 0)}")
        else:
            st.error(f"Execution Failed: {res.get('error', 'Unknown Error')}")
