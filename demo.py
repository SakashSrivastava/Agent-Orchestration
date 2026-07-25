# demo.py — flagship scenario: research a company on the live web, then draft
# a tailored outreach note. The file write pauses for human approval.
from pathlib import Path
from executor import run_task

Path("workspace").mkdir(exist_ok=True)
Path("workspace/profile.txt").write_text(
    "Sakash Srivastava - AI engineer. Built a from-scratch multi-agent "
    "orchestration system: supervisor/specialist/reviewer agents, tool use, "
    "human-in-the-loop approvals, SQLite-backed crash recovery, and a Streamlit "
    "observability dashboard. Also experienced with PyTorch (medical image "
    "segmentation) and full-stack automation (Next.js, Playwright). "
    "Looking for AI engineering roles.",
    encoding="utf-8")

company = input("Company to research (press Enter for 'Anthropic'): ").strip() or "Anthropic"

result = run_task(
    f"Use web search to find out what {company} does and one recent piece of news "
    f"about them. Read profile.txt to learn about the candidate. Then write a short, "
    f"specific outreach note to outreach.txt, written in first person AS the candidate "
    f"and addressed to the {company} team, connecting the candidate's experience to "
    f"what {company} is working on. Do not exceed 150 words in the note."
)

if result is None:
    print("\nThe note is waiting for your approval:")
    print("  python approve.py            (CLI)")
    print("  streamlit run dashboard.py   (browser buttons)")
else:
    print("\n" + result)
