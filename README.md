# 🧠 Gradio + Ollama + MCP: Privacy-Aware Local LLM Agent Demo

## Overview

This project demonstrates how to build a **privacy-aware, locally hosted LLM agent** that uses [Ollama](https://ollama.com/) (for running LLMs on your hardware), the **Model Context Protocol (MCP)** for safe tool calling, and [Gradio](https://www.gradio.app/) for a conversational web UI—all powered by a local SQLite database and exposed as both an agent and an MCP server.

### Key Concepts

* **Model Context Protocol (MCP):**

  * An open protocol that lets LLMs “call” local or remote tools as APIs—standardizing how tools (DBs, functions, search, etc.) are plugged into LLM workflows.
  * MCP allows *privacy-respecting, auditable* tool use, as all function calls and data access can be monitored locally.

* **Localized Ollama LLM:**

  * Ollama lets you run state-of-the-art LLMs (like Granite, Llama 3, Qwen, etc.) *entirely on your machine*—no data leaves your computer.
  * This project uses the [Granite 3.1 MoE model](https://ollama.com/library/granite) for local inference.

* **Privacy-Aware Agent:**

  * Your queries and data never leave your device.
  * All tools and database operations are *locally executed*.
  * The architecture is compatible with edge devices and self-hosted deployment.

---

## Architecture

* **`server.py`** — launches a FastMCP MCP server exposing database tools over HTTP.
* **`client.py`** — runs a Gradio chat UI and connects a local LLM (via Ollama) to the MCP tools for tool-augmented responses.

---
### High-level Flow

1. **User interacts** via Gradio UI (`client.py`).
2. **Agent** uses Ollama LLM + MCP client to invoke tools (e.g., read/write SQLite).
3. **MCP server** (`server.py`) exposes the tool API (add\_data/read\_data) and executes SQL on your local DB.
4. **All logic and data** remain private and local.

---
## 🖥️ System Configuration

**Operating System**  
- Ubuntu 24.04 LTS  
- Kernel: `6.11.0-25-generic`  
- Architecture: `x86_64` (64-bit)

**Processor (CPU)**  
- Model: 13th Gen Intel® Core™ i9-13950HX  
- Cores: 24 cores / 32 threads  
- Max Frequency: 5.50 GHz  
- Virtualization: VT-x supported  
- L1 Cache: 896 KiB (Data), 1.3 MiB (Instruction)  
- L2 Cache: 32 MiB  
- L3 Cache: 36 MiB  

**Graphics (GPU)**  
- NVIDIA RTX 5000 Ada Generation  
- VRAM: 16 GB  
- Driver Version: 550.144.03  
- CUDA Version: 12.4  

**Python Environment**  
- Python Version: 3.11.9  
- Virtual Environment: `python -m venv mcpollama`

**Misc**  
- Virtualization Capabilities: Enabled (VT-x)  
- NUMA Nodes: 1 (all CPUs in node0: 0–31)  


---
## server.py — MCP Server for SQLite

**Purpose:**
Expose SQLite as a set of tools (`add_data`, `read_data`) via MCP so any MCP-compatible LLM agent can safely query/update the database.

**Highlights:**

* Uses [FastMCP](https://github.com/fastmcp/fastmcp) for quick MCP server setup.
* Initializes SQLite, creates two tables: `people` and `interactions`.
* Exposes two tools:

  * `add_data(query)`: Insert any SQL row (for demo purposes; could be restricted for production).
  * `read_data(query)`: Run SQL SELECT queries and return results.
* Designed for *local* usage; easy to swap DBs or add more tools.

**Code Summary:**

```python
import sqlite3
from fastmcp import FastMCP

# Create and configure MCP server
mcp = FastMCP(name="SQLiteMCPServer", port=8000, transport="streamable-http", ...)

# Setup SQLite
...

# Tool: Insert SQL record
@mcp.tool(name="add_data", ...)
def add_data(query: str) -> bool:
    ...

# Tool: Query records
@mcp.tool(name="read_data", ...)
def read_data(query: str = "SELECT * FROM people") -> list:
    ...

# Start server
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
```

---

## client.py — Gradio Chatbot with MCP-Aware Ollama Agent

**Purpose:**
A Gradio chatbot interface powered by a *local* LLM (via Ollama) that can autonomously call MCP-exposed database tools (add/read) as part of its workflow.

**Highlights:**

* **Ollama LLM:** Runs `granite3.1-moe` locally—no data sent to external servers.
* **MCP Client:** Connects to the MCP server at `http://127.0.0.1:8000/mcp` and loads available tools dynamically.
* **FunctionAgent:** An LLM agent (via `llama_index`) that can use both language reasoning and tool-calling to fulfill queries.
* **Gradio UI:** Simple chat interface + recent interactions display.
* **Full local logging:** Each user-agent chat and tool call is logged to SQLite for auditability and privacy.

**Code Structure:**

```python
# Import LLM (Ollama), MCP client, Gradio, etc.
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import FunctionAgent
from gradio.queueing import Queue
...

# Set up Ollama LLM
llm = Ollama(model="granite3.1-moe", ...)

# Connect to MCP server, get tool specs
mcp_client = BasicMCPClient("http://127.0.0.1:8000/mcp")
mcp_spec = McpToolSpec(client=mcp_client)

# Initialize FunctionAgent with loaded tools
agent = FunctionAgent(...)

# Gradio UI: Chatbot, input, buttons, history display
with gr.Blocks(...):
    ...

# Message handling: Sends chat to agent, which may call tools, logs all activity
def handle_message(...):
    ...
```


## How to Run Locally

The entire application is designed to run inside a dedicated Python virtual environment (`mcpollama`).
**Assumptions:**

* Ollama is already installed (using `curl -fsSL https://ollama.com/install.sh | sh`).
* The model `granite3.1-moe` is already pulled (`ollama pull granite3.1-moe`).

### Step-by-Step Instructions

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv final1
   source final1/bin/activate
   ```

2. **Install Python requirements:**

   ```bash
   pip install -r requirements.txt
   ```

 ![image](https://github.com/user-attachments/assets/356acaa6-f804-4dab-9b76-d90ad856c6a0)


3. **Start the MCP server (in terminal 1):**

   ```bash
   python server.py
   ```

   ![image](https://github.com/user-attachments/assets/7f0b57d7-d839-4037-98c0-d1b2aaf5eb15)


4. **Start Ollama (in a separate terminal, if not already running):**

   ```bash
   ollama serve
   ```

5. **Launch the Gradio chat UI (in terminal 2):**

   ```bash
   python client.py
   ```
![image](https://github.com/user-attachments/assets/a27971bd-4d96-41f8-b9ff-ea921defe0ba)

6. **Open the Gradio web interface**
   Navigate to the link shown in your terminal (typically [http://127.0.0.1:7860](http://127.0.0.1:7860)).

![image](https://github.com/user-attachments/assets/3691a174-c91a-4478-bceb-ac75a5fc57ae)


7. **Check sqlitebrowser demo.db**

![image](https://github.com/user-attachments/assets/67e51b2b-93a6-4f00-b69d-85690041cdc6)

---

**Tip:**
Keep your `mcpollama` virtual environment activated whenever running these scripts to avoid conflicts with system Python packages.
If you need to (re)pull the Ollama model:

```bash
ollama pull granite3.1-moe
```



---

## Privacy & Security Notes

* **Everything runs locally** (code, model, and data): *No cloud inference, no remote DBs unless you configure it!*
* **All tool calls** are routed via the MCP server, making tool invocation explicit and monitorable.
* **No user data is sent externally** unless you specifically write a tool that does so.

---

## MCP + Ollama + Gradio: What’s Unique?

* **Local LLM Reasoning:**
  The agent is *truly private*—your prompts, data, and results are never seen by any third party.

* **Composable Tool Use:**
  You can add more tools (APIs, custom Python functions, etc.) as MCP endpoints and the agent will auto-discover them.

* **Reproducible for hackathons, research, and teaching**
  Easily demo local LLM agent autonomy and privacy with minimal setup.

---

## Example Use Cases

* Query people in the database:
  “Who are all doctors over 30?”

* Add a new person:
  “Add a person named Akash, age 35, profession scientist.”

* View tool call traces and timing for debugging and research.

---

## License

Apache-2.0

---

## Credits

* Partha Pratim Ray (2025 Gradio Agents & MCP Hackathon)
* [Ollama](https://ollama.com/), [Gradio](https://gradio.app/), [FastMCP](https://github.com/fastmcp/fastmcp), [LlamaIndex](https://github.com/run-llama/llama_index)

---
