from mcp.server.fastmcp import FastMCP
import requests
mcp=FastMCP("stock") ## this is server name

@mcp.tool()
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json()
if __name__=='__main__':
    mcp.run(transport='streamable-http') 