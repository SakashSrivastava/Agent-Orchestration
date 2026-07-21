import json
from llm import client, DEFAULT_MODEL
from tools import TOOL_SCHEMAS, TOOL_FUNCTIONS

def run_with_tools(prompt: str, system: str="", model: str=DEFAULT_MODEL, max_steps: int=8) -> str:
    messages=[]
    if system:
        messages.append({"role":"system", "content": system})
    messages.append({"role":"user", "content": prompt})

    for step in range(max_steps):
        response=client.chat.completions.create(
            model=model,
            max_tokens=1024,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        msg=response.choices[0].message
        if not msg.tool_calls:
            return msg.content

        messages.append(msg)
        for tc in msg.tool_calls:
            name=tc.function.name
            args=json.loads(tc.function.arguments)
            print(f" [step {step+1}] {name}({args})")

            fn=TOOL_FUNCTIONS.get(name)
            try:
                result=fn(**args) if fn else f"Error: unknown tool '{name}'"
            except Exception as e:
                result=f"Error: {e}"

            messages.append({
                "role":"tool",
                "tool_call_id":tc.id,
                "content":str(result),
            })
    return "Error: agent exceeded max_steps without finishing"