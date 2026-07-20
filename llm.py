import os
import time
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
import json
from typing import Type, TypeVar

T=TypeVar("T", bound=BaseModel)
load_dotenv()
client=OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",   
)

PRICES={
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "llama-3.1-8b-instant" : (0.05, 0.08),
}
DEFAULT_MODEL="llama-3.3-70b-versatile"

class LLMResponse(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    cost_usd: float

def call_llm(
    prompt: str,
    system: str="",
    model: str=DEFAULT_MODEL,
    max_tokens: int=1024,
) -> LLMResponse:
    messages=[]
    if system:
        messages.append({"role":"system", "content":system})
    messages.append({"role":"user", "content":prompt})

    start=time.perf_counter()
    response=client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )
    latency=time.perf_counter()-start

    in_tok=response.usage.prompt_tokens
    out_tok=response.usage.completion_tokens
    price_in, price_out=PRICES.get(model, (0.0, 0.0))
    cost=(in_tok*price_in + out_tok*price_out)/1_000_000

    return LLMResponse(
        text=response.choices[0].message.content,
        model=model,
        input_tokens=in_tok,
        output_tokens=out_tok,
        latency_s=round(latency, 3),
        cost_usd=round(cost, 6),
    )

def call_llm_structured(
    prompt: str,
    schema: Type[T],
    system: str = "",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
    max_retries: int = 2,
) -> T:
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    full_system = (
        f"{system}\n\n"
        "Reply with a single JSON object only - no prose, no markdown fences.\n"
        f"The JSON must match this schema exactly:\n{schema_json}"
    )

    last_error = ""
    for attempt in range(max_retries + 1):
        full_prompt = prompt
        if last_error:
            full_prompt = (
                f"{prompt}\n\n"
                f"Your previous reply was invalid: {last_error}\n"
                "Fix it and reply with valid JSON only."
            )

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": full_prompt},
            ],
        )
        raw = response.choices[0].message.content

        try:
            return schema.model_validate_json(raw)
        except Exception as e:
            last_error = str(e)[:300]

    raise ValueError(f"Model failed to produce valid JSON after {max_retries + 1} attempts: {last_error}")