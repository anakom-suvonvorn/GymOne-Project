from mcp.server import Server
from mcp.types import Tool

server = Server("gym one system")

@server.tool()
def get_member(member_id: str):
    """Get gym member info"""
    return {"member_id": member_id, "name": "Bob"}

if __name__ == "__main__":
    server.run()