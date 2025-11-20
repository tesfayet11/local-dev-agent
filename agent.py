# agent.py
# import os
# import json
# from dotenv import load_dotenv
# from openai import OpenAI
#
# from pathlib import Path
#
#
# from tools import filesystem, shell, postgres

# # load_dotenv()
# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(BASE_DIR / ".env")

# agent.py
import json

from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # explicitly load .env next to agent.py

from openai import OpenAI
from tools import filesystem, shell, postgres

client = OpenAI()

SYSTEM_PROMPT = """
You are a local Software Engineering assistant running on the user's machine.

You can:
- Read and write files in the user's project root.
- Run shell commands (mvn, npm, tests, etc.).
- Query a local Postgres database.

Goals:
- Help with Java/Spring/Angular/React/Next.js/AWS work.
- Be concise but clear.
- Before big refactors, explain your plan briefly.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file from the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from PROJECT_ROOT"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a text file to the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "overwrite": {"type": "boolean", "default": True},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files under a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "."},
                    "max_files": {"type": "integer", "default": 200},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command in the project root (e.g., mvn test, npm run build).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "integer", "default": 120},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run a SQL query on the local Postgres database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "params": {
                        "type": "array",
                        "items": {},
                        "description": "Positional parameters for the SQL query",
                        "default": [],
                    },
                    "fetch": {
                        "type": "string",
                        "enum": ["auto", "all", "one", "none"],
                        "default": "auto",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

def call_tool(name: str, arguments: dict):
    if name == "read_file":
        return filesystem.read_file(**arguments)
    if name == "write_file":
        return filesystem.write_file(**arguments)
    if name == "list_files":
        return filesystem.list_files(**arguments)
    if name == "run_command":
        return shell.run_command(**arguments)
    if name == "run_sql":
        return postgres.run_sql(**arguments)
    return {"error": f"Unknown tool {name}"}

def main():
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    print("💻 Local Dev Agent (with Postgres). Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})

        # First call: let the model decide if it needs tools
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = resp.choices[0].message

        if msg.tool_calls:
            # Handle tool calls one by one, then call model again with results
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                print(f"\n[tool] Calling {fn_name} with {args}")
                result = call_tool(fn_name, args)

                messages.append(
                    {
                        "role": "assistant",
                        "tool_calls": [tool_call],
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "name": fn_name,
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

            # Second call: let model respond with final answer using tool output
            final_resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
            )
            final_msg = final_resp.choices[0].message
            print(f"\nAgent: {final_msg.content}\n")
            messages.append({"role": "assistant", "content": final_msg.content})
        else:
            print(f"\nAgent: {msg.content}\n")
            messages.append({"role": "assistant", "content": msg.content})


if __name__ == "__main__":
    main()
