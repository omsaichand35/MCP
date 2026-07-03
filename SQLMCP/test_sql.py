import json

from MCP.SQLMCP.executor import classify_query, explain_query, run_and_record_query
from MCP.SQLMCP.ollama_client import generate_sql
from MCP.SQLMCP.validator import validate_sql


def run_sql_pipeline(question: str) -> dict:
	answer = generate_sql(question)
	validation = validate_sql(answer)
	query_type = classify_query(answer)
	explanation = explain_query(answer)

	response = {
		"question": question,
		"sql": answer,
		"query_type": query_type,
		"validation": validation,
		"explanation": explanation,
	}

	if not validation["valid"]:
		response["result"] = {
			"success": False,
			"error": "SQL validation failed.",
		}
		run_and_record_query(question, answer, validation, approved=False)
		return response

	if query_type in {"WRITE", "ADMIN"}:
		approval = input("Approve write execution? (yes/no): ").strip().lower()
		approved = approval in {"yes", "y"}
		response["approved"] = approved
		response["result"] = run_and_record_query(question, answer, validation, approved=approved)
		return response

	response["result"] = run_and_record_query(question, answer, validation, approved=True)
	return response


if __name__ == "__main__":
	question = input("Enter your SQL question: ").strip()
	output = run_sql_pipeline(question)
	print(json.dumps(output, indent=2, default=str))