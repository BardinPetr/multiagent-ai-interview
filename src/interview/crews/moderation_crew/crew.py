from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from interview.config.settings import settings
from interview.config.utils import kickoff
from interview.state import GuardClassificationResult, InterviewState, GuardCategory


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
            llm=settings.llm
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


def kickoff_moderator(crew, state: InterviewState, candidate_text) -> GuardClassificationResult:
    return kickoff(
        crew,
        dict(
            interview_topic=state.interview_topic,
            interviewer_message=state.current_question,
            candidate_message=candidate_text
        )
    ) or GuardClassificationResult(category=GuardCategory.IRRELEVANT)
