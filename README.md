# Episode 11 — AI On-Call Agent I: Tools (the agent's hands)

So far our AI could only *talk* — explain a log, answer from a runbook. An **agent** can
*act*: it can check a service's status, tail logs, hit a health endpoint, read metrics. This
episode builds those **hands** — four **read-only** ops tools — and shows the model **choosing
and calling** them. The multi-step investigation *loop* is Episode 12; the *write* actions and
approval gates are Episode 13.

## The one mental model (kills the "AGI" myth)

> **The LLM does not run your tools. It *asks*. Your code runs them.**

An agent is not a magical autonomous brain. It's a plain loop: the **LLM decides** which tool
to call, **your code executes** it, the **result goes back**, and it decides again. You are
always in control of what can actually run — which is exactly why we start **read-only**.

```
question -> [LLM: which tool?] -> tool_call -> [YOUR code runs a read-only tool] -> result -> [LLM answers]
```

## Read-only by default (the most important line in this module)

Every tool here can **look, not touch**: `get_service_status`, `tail_logs`, `get_metrics`,
`http_check`. Nothing restarts, deletes, scales, or deploys. Giving an agent write access
without guardrails is how you get the "AI ran `kubectl delete ns prod`" nightmare — so we
earn trust with read-only first, then add gated writes in Episode 13.

## Files

| File | What it shows | Needs a key? |
|------|---------------|--------------|
| `_tools.py` | The 4 read-only tools + their function-calling schemas + a `dispatch()`. | no |
| `sample_ops/` | A baked-in incident: **checkout crashed (OOMKilled) → nginx 502s**. | no |
| `03_run_tools_directly.py` | Run the tools with **no AI** — prove they work and only read. | no |
| `01_one_tool.py` | Give the model one tool; watch it *ask* to call it (it doesn't run it). | yes |
| `02_call_tools.py` | One full round: model calls tools → code runs them → grounded answer. | yes |
| `ask-ops.py` | **The tool** — ask an on-call question, see which read-only tools it used. | yes |

## Setup & run

```bash
pip install -r requirements.txt
cp .env.example .env          # paste your free Groq key (Windows: copy)

python 03_run_tools_directly.py                 # no key needed
python ask-ops.py "why is the site returning 502 on checkout?"
python ask-ops.py "is payments healthy?"
```

Groq's `openai/gpt-oss-120b` supports OpenAI-style tool calling. The tool-calling code is
standard and works unchanged against real OpenAI; only `base_url` + model differ.

## How the sample incident reads (so you can check the agent)

`sample_ops/` encodes one consistent story, so you can verify the agent isn't guessing:

- `get_service_status("checkout")` → `crashed`, 0/2 replicas, `OOMKilled (exit 137)`.
- `tail_logs("checkout")` → `MemoryError` → `OOMKilled`.
- `http_check(".../api/checkout")` → `502` (upstream checkout down).
- `get_metrics("nginx")` → error rate 68%, "5xx from upstream failures".

A good answer names the real cause (checkout OOMKilled) and proposes a **human-reviewed** fix.

## Honesty & limits (please keep these in the video)

- **The tools are simulated over sample data** so the episode runs offline. `http_check` is a
  stub — the file shows the one-line real version (`requests.get(url).status_code`). Point the
  other tools at real read-only commands/APIs the same way; the schemas don't change.
- **Read-only is a real safety boundary, not a formality.** The model literally cannot run
  anything outside `IMPLS`, and nothing in `IMPLS` mutates state.
- **The model can still be wrong.** Tools give it facts; it can still misread them. Anything it
  proposes to *change* must be reviewed by a human — enforced properly in Episode 13.
- **Tool calling is model- and provider-dependent.** Behavior and JSON formatting can vary by
  model; test your prompts on the model you deploy.
