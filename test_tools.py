from tool_agent import run_with_tools

answer = run_with_tools(
    "Calculate 17.5% of 2840. Then write a file called tax.txt containing "
    "the result with a one-sentence explanation. Then tell me what you did."
)
print("\nFINAL ANSWER:", answer.text)
print("\nTOOL LOG:", *answer.tool_log, sep="\n  ")
print("\nFILE CONTENTS:", open("workspace/tax.txt", encoding="utf-8").read())