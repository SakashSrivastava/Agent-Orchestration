from supervisor import make_plan
from schemas import execution_order

plan = make_plan(
    "Read the numbers in data.txt, calculate their total plus 18% GST, "
    "and write an invoice summary to invoice.txt"
)

print(f"GOAL: {plan.goal}\n")
for s in plan.subtasks:
    deps = f" (needs {s.depends_on})" if s.depends_on else ""
    print(f"  [{s.id}] {s.specialist}: {s.description}{deps}")

print(f"\nEXECUTION WAVES: {execution_order(plan)}")