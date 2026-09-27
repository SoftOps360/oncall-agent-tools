"""ask-ops - ask an on-call question; the assistant uses READ-ONLY tools to answer from facts.

  python ask-ops.py "is checkout healthy?"
  python ask-ops.py "why is the site returning 502 on checkout?"

It runs ONE round of tool use (Think -> Act -> Observe) and shows exactly which tools it
called, so nothing is hidden. Every tool is read-only - it can look, never change.
The multi-step investigation LOOP is Episode 12; the write actions + approval gates are Episode 13.
"""
import sys
import json
from _llm import client, MODEL
from _tools import TOOLS, dispatch

SYSTEM = ("You are an on-call SRE assistant. Use the read-only tools to gather facts before "
          "answering. Base your answer only on tool results; never invent status, logs, or "
          "numbers. If you propose a fix, say it must be reviewed by a human before running.")


def main():
    question = " ".join(sys.argv[1:]).strip() or sys.stdin.read().strip()
    if not question:
        print('Usage: python ask-ops.py "your on-call question"')
        return

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]

    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto")
    msg = resp.choices[0].message
    messages.append(msg)

    if msg.tool_calls:
        print("[the assistant used these read-only tools]")
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = dispatch(call.function.name, args)
            print(f"  - {call.function.name}({args})")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
        msg = client.chat.completions.create(model=MODEL, messages=messages).choices[0].message

    print("\n" + (msg.content or ""))


if __name__ == "__main__":
    main()
