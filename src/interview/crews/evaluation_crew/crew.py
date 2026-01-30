from typing import List, Dict

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from interview.state import InterviewState, EvaluatorContext, SoftSkillScores


@CrewBase
class EvaluationCrew:
    """Crew for generating final evaluation_crew and feedback"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def evaluator(self) -> Agent:
        return Agent(
            config=self.agents_config['evaluator'],
            verbose=False
        )

    @agent
    def softskills_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config['softskills_assessor'],
            allow_delegation=False,
            verbose=False
        )

    @agent
    def fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['fact_checker'],
            allow_delegation=False,
            verbose=False,
        )

    """"""

    @task
    def initial_evaluation(self) -> Task:
        return Task(
            config=self.tasks_config['initial_evaluation'],
            context=[],
            agent=self.evaluator()
        )

    @task
    def softskills_assessment(self) -> Task:
        return Task(
            config=self.tasks_config['softskills_assessment'],
            output_pydantic=SoftSkillScores,
            context=[self.initial_evaluation()],
            agent=self.softskills_assessor()
        )

    @task
    def fact_checking(self) -> Task:
        return Task(
            config=self.tasks_config['fact_checking'],
            context=[self.initial_evaluation()],
            agent=self.fact_checker()
        )

    @task
    def final_evaluation(self) -> Task:
        return Task(
            config=self.tasks_config['final_evaluation'],
            output_pydantic=EvaluatorContext,
            context=[
                self.initial_evaluation(),
                self.softskills_assessment(),
                self.fact_checking()
            ],
            agent=self.evaluator()
        )

    """"""

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False
        )


def kickoff_qa_evaluation(crew, state: InterviewState) -> EvaluatorContext:
    inputs = evaluate_answer_input(state)
    res = crew.crew().kickoff(inputs=inputs)
    return res.pydantic


def evaluate_answer_input(state: InterviewState) -> Dict:
    return dict(
        candidate_info=state.candidate.model_dump_json(),
        valid_answer='not computed yet',
        question=state.current_question,
        answer=state.candidate_answer,
        reasoning=None,
        softskills=None,
        fact_check_results=None,
        needs_correction=None,
        initial_score=None,
        topic=None,
    )
