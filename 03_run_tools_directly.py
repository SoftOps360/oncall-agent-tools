"""Step 0 - the tools by themselves, with NO AI. Prove they work and are read-only.

An agent is only as good as its hands. Before we let the LLM call these, we run them
ourselves and read the output. Notice they only ever LOOK - none of them change anything.
"""
from _tools import get_service_status, tail_logs, get_metrics, http_check

print("get_service_status('checkout'):")
print(" ", get_service_status("checkout"))

print("\nget_metrics('nginx'):")
print(" ", get_metrics("nginx"))

print("\nhttp_check('https://shop.example.com/api/checkout'):")
print(" ", http_check("https://shop.example.com/api/checkout"))

print("\ntail_logs('checkout', 4):")
for ln in tail_logs("checkout", 4)["lines"]:
    print("   ", ln)

print("\nThese four read-only tools are the agent's hands. In Episode 12 the LLM will decide "
      "WHICH to call, in a loop, to investigate an incident on its own.")
