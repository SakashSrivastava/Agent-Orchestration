from pathlib import Path

WORKSPACE=Path("workspace")
WORKSPACE.mkdir(exist_ok=True)

def _safe_path(filename: str) -> Path:
    path=(WORKSPACE/filename).resolve()
    if WORKSPACE.resolve()!=path.parent and WORKSPACE.resolve() not in path.parents:
        raise ValueError(f"Access outside workspace/ is not allowed: {filename}")
    return path

def calculator(expression: str) -> str:
    if not set(expression) <= set("0123456789+-*/.() ") or "**" in expression or len(expression)>100:
        return "Error: only basic arithmetic is allowed"
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"
    
def write_file(filename: str, content: str) -> str:
    path=_safe_path(filename)
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {filename}"

def read_file(filename: str) -> str:
    path=_safe_path(filename)
    if not path.exists():
        return f"Error: {filename} does not exist"
    return path.read_text(encoding="utf-8")

def web_search(query: str) -> str:
    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No results found."
        lines = [f"- {r.get('title', '')}: {r.get('body', '')[:250]} ({r.get('href', '')})"
                 for r in results]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: web search failed - {e}"

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. '17.5 / 100 * 2840'",
        "parameters": {"type": "object",
                       "properties": {"expression": {"type": "string"}},
                       "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write text content to a file in the workspace",
        "parameters": {"type": "object",
                       "properties": {"filename": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["filename", "content"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from the workspace",
        "parameters": {"type": "object",
                       "properties": {"filename": {"type": "string"}},
                       "required": ["filename"]}}},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Search the live web. Returns the top results as titles with "
                       "snippets and URLs. Use focused queries, e.g. 'Anthropic recent news'",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}},
]

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "write_file": write_file,
    "read_file": read_file,
    "web_search": web_search,
}