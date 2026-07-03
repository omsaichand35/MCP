from ollama import Client
import json

from prompts import SYSTEM_PROMPT
from database import get_live_schema

client = Client()
MODEL = "qwen3.5:latest"


def generate_sql(question: str) -> str:
    schema = get_live_schema()

    prompt = f"""
Database Schema:
{schema}

User Request:
{question}

Generate a SQL Server query using ONLY the tables and columns
provided in the schema.

Return ONLY SQL.
No explanation.
No markdown.
No code fences.
"""

    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"].strip()


def generate_schema_from_prompt(prompt: str):
    """
    Sends a prompt to the LLM to generate a structured JSON schema.
    """
    system_prompt = """
    You are a database architect. The user will provide a natural language
    description of a database schema. Your job is to convert this into a
    structured JSON object.

    The JSON object should have table names as keys.
    Each value should be an array of column names for that table.

    - Infer appropriate column names from the description.
    - Identify primary keys and foreign keys from the relationships described.
    - Do not add any extra explanations, just return the raw JSON object.

    Example user prompt:
    "I need a database for a blog. It should have users (with id, name, email) and posts (with id, title, content, and user_id as a foreign key to users)."

    Example JSON output:
    {
      "users": ["id", "name", "email"],
      "posts": ["id", "title", "content", "user_id"]
    }
    """
    response = client.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    # Extract the JSON part from the response
    json_str = response['message']['content']
    try:
        # The model might return the JSON inside a code block
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Error decoding schema JSON from LLM response: {e}")
        print(f"Raw response: {json_str}")
        return None