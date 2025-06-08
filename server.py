# server.py
# Partha Pratim Ray, 8 June, 2025, parthapratimray1986@gmail.com

import sqlite3
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(
    name="SQLiteMCPServer",
    port=8000,
    transport="streamable-http",
    instructions="Tools: add_data(query) and read_data(query)."
)

# --- Database Setup ---
DB_PATH = "demo.db"
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_cursor = _conn.cursor()

print("🔧 Connecting to SQLite DB:", DB_PATH)

# Create tables
print("🛠️ Ensuring table 'people' exists…")
_cursor.execute("""
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        profession TEXT NOT NULL
    )
""")

print("🛠️ Ensuring table 'interactions' exists…")
_cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT NOT NULL,
        response TEXT NOT NULL,
        time_taken_sec REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

_conn.commit()
print("✅ Tables are ready.")


# --- Tool: Add Record ---
@mcp.tool(name="add_data", description="Insert a record via SQL")
def add_data(query: str) -> bool:
    print(f"📥 [add_data] Executing query:\n{query}")
    try:
        _cursor.execute(query)
        _conn.commit()
        print("✅ Inserted successfully.")
        return True
    except Exception as e:
        print(f"❌ Insert error: {e}")
        return False


# --- Tool: Read Records ---
@mcp.tool(name="read_data", description="Query records via SQL")
def read_data(query: str = "SELECT * FROM people") -> list:
    print(f"📤 [read_data] Executing query:\n{query}")
    try:
        _cursor.execute(query)
        results = _cursor.fetchall()
        print(f"✅ Retrieved {len(results)} rows.")
        return results
    except Exception as e:
        print(f"❌ Read error: {e}")
        return []


# --- Run the Server ---
if __name__ == "__main__":
    print("🚀 Starting SQLite MCP server on http://127.0.0.1:8000 …")
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)

