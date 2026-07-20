from llm import call_llm

r=call_llm("Say hello in exactly five words.")
print(r.text)
print(f"tokens: {r.input_tokens} in/{r.output_tokens} out")
print(f"cost if paid: ${r.cost_usd} latency: {r.latency_s}s")
