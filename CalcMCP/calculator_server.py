from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator")

@mcp.tool()
def add(a: int, b: int) -> int:
    """ Adds two numbers together """
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """ Subtracts two numbers together """
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """ Multiplies two numbers together """
    return a * b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """ Divides two numbers together """
    if b == 0:
        raise ValueError("Divide by zero")

    return a / b


if __name__ == "__main__":
    mcp.run()