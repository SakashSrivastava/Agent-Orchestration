from pathlib import Path
from executor import run_task, resume_task

Path("workspace").mkdir(exist_ok=True)
Path("workspace/data.txt").write_text("1200\n850\n2300\n475\n", encoding="utf-8")

task = ("Read the numbers in data.txt, calculate their total plus 18% GST, "
        "and write an invoice summary to invoice.txt")

print("=== PHASE 1: run until pause after subtask 1 ===")
run_task(task, stop_after=1)

task_id = input("\nEnter the task id shown above to resume it: ").strip()

print("\n=== PHASE 2: resume from disk ===")
final = resume_task(task_id)
print("\nFINAL:", final)
