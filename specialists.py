from tools import TOOL_SCHEMAS

SPECIALISTS={
    "researcher": {
        "system": "You are a research specialist. Use read_file to gather the "
                  "information your subtask asks for, then report exactly what you "
                  "found. Never invent data that is not in the files.",
        "tools" : ["read_file"],
    },
    "analyst" : {
        "system" : "You are a numerical analyst. Use the calculator tool for every "
                   "calculation - never do arithmetic in your head, even easy "
                   "arithmetic. Report the computed values clearly",
        "tools" : ["calculator"],
    },
    "writer" : {
        "system" : "You are a writing specialist. Use write_file to produce the "
                   "requested file. Base your content only on the context you are "
                   "given. Confirm the filename and what you wrote.",
        "tools" : ["write_file"],
    },
}


def schemas_for(names: list[str]) -> list[dict]:
    return [s for s in TOOL_SCHEMAS if s["function"]["name"] in names]