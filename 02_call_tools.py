"""Step 2 - one full round of tool use: the model may call SEVERAL read-only tools, our code
runs each, we hand the results back, and the model writes a final grounded answer.

This is ONE Think -> Act -> Observe step. Episode 12 turns this into a loop so the agent can
follow a trail (status -> logs -> metrics) until it has the full picture.
"""
import json
from _llm import client, MODEL
from _tools import TOOLS, dispatch

SYSTEM = ("You are an on-call SRE assistant. Use the read-only tools to gather facts before "
          "answering. Base your answer only on tool results; do not guess. Be concise.")


def run(question):
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]

    # 1) Think: let the model decide which tools to call.
    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto")
    msg = resp.choices[0].message
    messages.append(msg)

    if not msg.tool_calls:
        return msg.content

    # 2) Act + Observe: run each requested tool and feed the results back.
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        result = dispatch(call.function.name, args)
        print(f"  [tool] {call.function.name}({args}) -> {result}")
        messages.append({"role": "tool", "tool_call_id": call.id,
                         "content": json.dumps(result)})

    # 3) Final answer, now grounded in real tool output.
    final = client.chat.completions.create(model=MODEL, messages=messages)
    return final.choices[0].message.content


if __name__ == "__main__":
    q = "The site is throwing 502s on checkout. What's wrong?"
    print(f"Q: {q}\n")
    print(run(q))
