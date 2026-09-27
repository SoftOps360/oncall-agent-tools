"""Step 1 - give the model ONE tool and watch it ASK to use it.

The key mental model: the LLM does NOT run your tool. It reads the tool's schema, decides it
needs it, and replies with a *request* - "please call get_service_status(service='checkout')".
Running it is YOUR code's job. That separation is what makes an agent safe to build.
"""
from _llm import client, MODEL
from _tools import TOOLS, dispatch

# Give it just the first tool for this demo.
one_tool = [TOOLS[0]]   # get_service_status

messages = [
    {"role": "system", "content": "You are an on-call assistant. Use tools to check facts before answering."},
    {"role": "user", "content": "Is the checkout service healthy right now?"},
]

resp = client.chat.completions.create(model=MODEL, messages=messages, tools=one_tool, tool_choice="auto")
msg = resp.choices[0].message

if msg.tool_calls:
    for call in msg.tool_calls:
        print("The model asked to call a tool (it did NOT run it):")
        print("  tool:", call.function.name)
        print("  args:", call.function.arguments)
        # Our code is what actually runs it:
        import json
        result = dispatch(call.function.name, json.loads(call.function.arguments))
        print("  our code ran it ->", result)
else:
    print("The model answered without a tool:")
    print(" ", msg.content)
