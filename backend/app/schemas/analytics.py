from pydantic import BaseModel
from typing import List


class PriorityDistribution(BaseModel):
    name: str
    value: int


class ProjectProgress(BaseModel):
    name: str
    total: int
    done: int
    pct: int


class AnalyticsResponse(BaseModel):
    totalTasks: int
    completedTasks: int
    activeTasks: int
    completionRate: int
    priorityDistribution: List[PriorityDistribution]
    projectProgress: List[ProjectProgress]
    totalActivity: int
    totalProposals: int
    pendingProposals: int