# MCP Projects

A collection of small Python examples for the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). Each directory is a separate experiment; there is no single application entry point.

## Projects

| Directory | Example |
| --- | --- |
| `Basic_MCP` | Text analysis tool exposed through MCP |
| `CalcMCP` | Calculator server |
| `FileSystemMCP` | File listing, search, read, write, copy, rename, and delete tools scoped to a sample workspace |
| `routeMCP` | Network route lookup tools |
| `SQLMCP` | Streamlit database copilot with schema inspection, SQL generation, validation, and query history |
| `subnetMCP` | IP subnet and address tools |
| `TerminalMCP` | MCP wrapper for running operating-system commands |
| `weatherMCP` | Weather lookup tools |

## Requirements

- Python 3.11 or newer
- Dependencies vary by project. The examples use the MCP Python SDK, OpenAI-compatible client, Requests, Streamlit, pandas, Ollama, SQLGlot, pyodbc, NumPy, and scikit-learn.
- `SQLMCP` also requires a SQL Server ODBC driver and a reachable SQL Server. Its language model integration uses a local Ollama service.
- The LLM-backed clients use the NVIDIA API through its OpenAI-compatible endpoint.

Install the Python dependencies from the repository root:

```sh
python -m venv .venv
python -m pip install -r requirements.txt
```

Activate the virtual environment before running an example. Some examples also need external software or services listed above. The dependencies are not pinned yet.

## API key setup

Set `NVIDIA_API_KEY` in your environment before starting any LLM-backed client. Do not commit the key or put it in source code.

PowerShell:

```powershell
$env:NVIDIA_API_KEY = "your-new-key"
python .\Basic_MCP\client.py
```

macOS or Linux:

```sh
export NVIDIA_API_KEY="your-new-key"
python Basic_MCP/client.py
```

The clients that need this key are in `Basic_MCP`, `FileSystemMCP`, `routeMCP`, `subnetMCP`, and `weatherMCP`.

## Security notes

These are learning examples, not hardened production services. Review each tool before connecting it to an MCP host or an LLM.

- `TerminalMCP` executes shell commands supplied to the tool. Run it only in a disposable, isolated environment; the process can access anything allowed to the current user.
- `FileSystemMCP` can write, rename, copy, and delete files in its workspace. Use test data and review paths before connecting it to an agent.
- `SQLMCP` can run database queries. Test against a disposable database and review its approval and validation flow before using real data.
- Never expose credentials, private datasets, or local database files in commits. If a credential has already been committed, revoke it and replace it; deleting it from the latest version does not remove it from Git history.

## Contributing

Contributions are welcome. Open an issue to discuss larger changes, and submit focused pull requests with a clear description of the example you changed and how you checked it. Do not include API keys, database contents, compiled Python files, or personal data.

## License

This project is proposed for release under the MIT License. See [LICENSE](LICENSE).
