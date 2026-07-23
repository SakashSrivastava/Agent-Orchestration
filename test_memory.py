from pathlib import Path
from executor import run_task
from memory import recall

Path("workspace").mkdir(exist_ok=True)
Path("workspace/data.txt").write_text("1200\n850\n2300\n475\n", encoding="utf-8")

print("=== TASK 1 (system has no memories yet) ===")
run_task("Read the numbers in data.txt, calculate their total plus 18% GST, "
         "and write an invoice summary to invoice.txt")

print("\nMemories now stored:")
for m in recall("invoice GST calculation", k=5):
    print(" -", m)

print("\n=== TASK 2 (similar task - watch for recall) ===")
run_task("Read data.txt, calculate the total with 12% GST, "
         "and write a bill summary to bill.txt")
