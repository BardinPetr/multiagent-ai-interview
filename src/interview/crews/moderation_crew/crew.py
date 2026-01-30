from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from interview.state import GuardClassificationResult


@CrewBase
class ModerationCrew:
    """ Первичная классификация запроса и безопасность  """

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def guard(self) -> Agent:
        return Agent(
            config=self.agents_config['guard'],
            verbose=False,
        )

    @task
    def classify_candidate_message(self) -> Task:
        return Task(
            config=self.tasks_config['classify_candidate_message'],
            agent=self.guard(),
            output_pydantic=GuardClassificationResult,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False
        )

