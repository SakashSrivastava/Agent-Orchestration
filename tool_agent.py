import json
import time
from openai import BadRequestError
from pydantic import BaseModel
from llm import client, log_call, DEFAULT_MODEL
from tools import TOOL_SCHEMAS, TOOL_FUNCTIONS


class AgentResult(BaseModel):
    text: str
    tool_log: list[str]


def run_with_tools(prompt: str, system: str="", model: str=DEFAULT_MODEL, max_steps: int=8, tools: list|None=None) -> AgentResult:
    tools = tools if tools is not None else TOOL_SCHEMAS
    tool_log: list[str] = []
    messages=[]
    if system:
        messages.append({"role":"system", "content": system})
    messages.append({"role":"user", "content": prompt})

    for step in range(max_steps):
        try:
            start=time.perf_counter()
            response=client.chat.completions.create(
                model=model,
                max_tokens=1024,
                messages=messages,
                tools=tools,
            )
            log_call(model, response.usage, time.perf_counter()-start, caller="tool_agent")
        except BadRequestError as e:
            if "tool_use_failed" in str(e):
                print(f"  [step {step+1}] malformed tool call from model - retrying")
                continue
            raise
        msg=response.choices[0].message
        if not msg.tool_calls:
            return AgentResult(text=msg.content, tool_log=tool_log)

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

            tool_log.append(f"{name}({tc.function.arguments}) -> {str(result)[:2000]}")

            messages.append({
                "role":"tool",
                "tool_call_id":tc.id,
                "content":str(result),
            })
    return AgentResult(text="Error: agent exceeded max_steps without finishing", tool_log=tool_log)