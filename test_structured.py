from pydantic import BaseModel
from llm import call_llm_structured

class Recipe(BaseModel):
    name: str
    cuisine: str
    prep_minutes: int
    ingredients: list[str]
    is_vegetarian: bool


r = call_llm_structured(
    prompt="Give me a simple recipe for masala chai.",
    schema=Recipe,
)

print(r)
print(f"\nFirst ingredient: {r.ingredients[0]}")
print(f"Prep time doubled: {r.prep_minutes * 2} minutes")