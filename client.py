# client.py


import re
import time
import sqlite3
import asyncio
import gradio as gr
from gradio.queueing import Queue

# Patch Gradio queue to avoid NoneType error
if not hasattr(gr.Blocks, "_queue") or gr.Blocks._queue is None:
    gr.Blocks._queue = Queue(
        live_updates=False,
        concurrency_count=1,
        update_intervals=[],
        max_size=64,
        blocks=None
    )

# Ollama import (new & legacy)
try:
    from llama_index.llms.ollama import Ollama
except ImportError:
    from llama_index.legacy.llms.ollama import Ollama

# MCP imports (new & legacy)
try:
    from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
except ImportError:
    from llama_index.legacy.tools.mcp import BasicMCPClient, McpToolSpec

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

llm = Ollama(model="granite3.1-moe", request_timeout=300.0)

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"
#MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/http"

mcp_client = BasicMCPClient(MCP_SERVER_URL)
mcp_spec = McpToolSpec(client=mcp_client)

async def init_agent():
    print("🔵 Fetching tools…")
    tools = await mcp_spec.to_tool_list_async()
    print(f"🔵 Loaded {len(tools)} tools.")
    agent = FunctionAgent(
        name="SQLiteAgent",
        description="Agent for SQLite people DB via MCP",
        tools=tools,
        llm=llm,
        system_prompt="You are an assistant. Use the tools to read/write the people database.",
    )
    print("🔵 Agent ready.")
    return agent, Context(agent)

agent, agent_context = loop.run_until_complete(init_agent())
print("✅ Agent & Context initialized.")


def clean_response(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)
    return cleaned.strip()

async def async_handle_message(msg: str) -> str:
    print(f"\n🟢 USER: {msg}")
    handler = agent.run(msg, ctx=agent_context)
    async for event in handler.stream_events():
        if hasattr(event, "tool_name"):
            print(f"🔧 ToolCall → {event.tool_name}")
    try:
        raw = await handler
        raw_text = str(raw)
    except Exception as e:
        raw_text = f"⚠️ [ERROR] {e}"
    print(f"🟣 RAW RESPONSE: {repr(raw_text)}")
    cleaned = clean_response(raw_text)
    print(f"🟣 CLEANED RESPONSE: {repr(cleaned)}")
    return cleaned or "⚠️ (empty response)"


def handle_message(message, chat_history):
    if not isinstance(chat_history, list) or any(not isinstance(m, dict) for m in chat_history):
        chat_history = []

    chat_history.append({"role": "user", "content": message})

    start = time.time()
    reply = loop.run_until_complete(async_handle_message(message))
    end = time.time()

    chat_history.append({"role": "assistant", "content": reply})

    try:
        db_conn = sqlite3.connect("demo.db")
        db_cursor = db_conn.cursor()
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                time_taken_sec REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db_cursor.execute(
            "INSERT INTO interactions (prompt, response, time_taken_sec) VALUES (?, ?, ?)",
            (message, reply, round(end - start, 3))
        )
        db_conn.commit()
        db_conn.close()
        print(f"[DB] Logged interaction in {round(end - start, 3)} sec")
    except Exception as e:
        print(f"[DB ERROR] {e}")

    return chat_history, ""


def fetch_recent_interactions(limit=5):
    try:
        conn = sqlite3.connect("demo.db")
        cursor = conn.cursor()
        cursor.execute("SELECT prompt, response, time_taken_sec, timestamp FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return [("Error fetching interactions", str(e), 0, "")]


with gr.Blocks(title="Gradio Agents & MCP Hackathon 2025") as demo:
    gr.Markdown("""
    # 🧠 SQLite MCP Chatbot — <span style='color:#4A90E2;'>Gradio + Ollama + MCP</span> 
    ### Designed by **Partha Pratim Ray** for the Gradio Agents & MCP Hackathon 2025 🚀
    """, elem_id="header")

    with gr.Row():
        with gr.Column():
            chatbot = gr.Chatbot(label="🗨️ Chat Window", type="messages", height=400)
            user_input = gr.Textbox(placeholder="Type your question…", show_label=False)
            submit_btn = gr.Button("Submit")
            clear_btn = gr.Button("Clear Chat")
        with gr.Column():
            gr.Markdown("### 📜 Recent Interactions (Last 5)")
            output_display = gr.HTML()

    def update_recent_display():
        rows = fetch_recent_interactions()
        display = "<div style='font-family:monospace;'>"
        for prompt, response, sec, ts in rows:
            display += f"<div style='margin-bottom:12px; padding:10px; border-left: 4px solid #4A90E2;'>"
            display += f"<strong>🕒 {ts}</strong><br><strong>Prompt:</strong> {prompt}<br><strong>Response:</strong> {response[:300]}...<br><strong>⏱ Time:</strong> {sec} sec"
            display += "</div>"
        return display + "</div>"

    def on_submit(msg, chat):
        new_chat, _ = handle_message(msg, chat)
        recent_html = update_recent_display()
        return new_chat, "", recent_html

    submit_btn.click(on_submit, inputs=[user_input, chatbot], outputs=[chatbot, user_input, output_display])
    user_input.submit(on_submit, inputs=[user_input, chatbot], outputs=[chatbot, user_input, output_display])
    clear_btn.click(lambda: ([], "", update_recent_display()), None, [chatbot, user_input, output_display])

    # Load recent on startup
    demo.load(update_recent_display, None, output_display)

if __name__ == "__main__":
    demo.launch()

