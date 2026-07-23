from pathlib import Path
from executor import run_task

Path("workspace").mkdir(exist_ok=True)
Path("workspace/data.txt").write_text("1200\n850\n2300\n475\n", encoding="utf-8")

result = run_task("Read the numbers in data.txt, calculate their total plus 18% GST, "
                  "and write an invoice summary to invoice.txt")

if result is None:
    print("\nTask is paused, waiting for a human. Next: python approve.py")
