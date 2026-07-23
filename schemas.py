from typing import Literal
from pydantic import BaseModel, Field

Specialist=Literal["researcher", "analyst", "writer"]

class Subtask(BaseModel):
    id: int
    description: str=Field(description="One clear instruction for the specialist")
    specialist: Specialist
    depends_on: list[int]=Field(default_factory=list,
                                description="IDs of subtasks that must finish first")
    
class Plan(BaseModel):
    goal: str=Field(description="The user's request, restated precisely")
    subtasks: list[Subtask]


def execution_order(plan: Plan) -> list[list[int]]:
    ids = {s.id for s in plan.subtasks}
    for s in plan.subtasks:
        for dep in s.depends_on:
            if dep not in ids:
                raise ValueError(f"Subtask {s.id} depends on {dep}, which does not exist")
            if dep == s.id:
                raise ValueError(f"Subtask {s.id} depends on itself")

    done: set[int] = set()
    waves: list[list[int]] = []
    while len(done) < len(plan.subtasks):
        wave = [s.id for s in plan.subtasks
                if s.id not in done and all(d in done for d in s.depends_on)]
        if not wave:
            raise ValueError("Dependency cycle detected - no subtask can proceed")
        waves.append(wave)
        done.update(wave)
    return waves

class Review(BaseModel):
    verdict: Literal["approve", "reject"]
    score: int = Field(ge=1, le=5, description="Quality score, 5 = flawless")
    feedback: str = Field(description="If rejecting, say exactly what to fix")