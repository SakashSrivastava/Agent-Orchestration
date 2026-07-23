from pathlib import Path
from executor import run_task

Path("workspace").mkdir(exist_ok=True)
Path("workspace/data.txt").write_text("1200\n850\n2300\n475\n", encoding="utf-8")

answer = run_task(
    "Read the numbers in data.txt, calculate their total plus 18% GST, "
    "and write an invoice summary to invoice.txt"
)

print("\n================ FINAL ANSWER ================")
print(answer)
print("\n================ INVOICE FILE ================")
print(Path("workspace/invoice.txt").read_text(encoding="utf-8"))