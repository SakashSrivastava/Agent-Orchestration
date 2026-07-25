from tools import TOOL_SCHEMAS

SPECIALISTS={
    "researcher": {
        "system": "You are a research specialist. Use read_file for workspace files "
                  "and web_search for anything on the internet. Report exactly what "
                  "you found, citing which source it came from. Never invent data "
                  "that is not in the files or search results.",
        "tools" : ["read_file", "web_search"],
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