from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from interview.config.settings import settings
from interview.state import InterviewState


@CrewBase
class FinalCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def final_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['final_analyst'],
            verbose=False,
            llm=settings.llm
        )

    @task
    def analyze(self) -> Task:
        return Task(
            config=self.tasks_config['analyze'],
            agent=self.final_analyst()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False
        )


def kickoff_final(crew, state: InterviewState):
    res = crew.crew().kickoff(inputs=dict(interview_state=state.model_dump_json()))
    return res.raw
