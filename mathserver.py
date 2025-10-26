from mcp.server.fastmcp import FastMCP

mcp=FastMCP("Math") ## this is server name

@mcp.tool()
def add(a: int, b:int)->int:
    """this is for adding two numbers"""
    return a+b
@mcp.tool()
def multiply(a: int, b:int)->int:
    """this is for multiply two numbers"""
    return a*b

if __name__=='__main__':
    mcp.run(transport='stdio') 