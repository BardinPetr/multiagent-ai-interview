from typing import List, Dict

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from interview.config.settings import settings
from interview.state import InterviewState, InterviewerUpdate


@CrewBase
class InterviewRuntimeCrew:
    """Crew for determining interview interview_runtime_crew and generating questions"""

    agents: List[BaseAgent]
    tasks: List[Task]

    """ interviewer """

    @agent
    def interviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['interviewer'],
            allow_delegation=True,
            verbose=False,
            llm=settings.llm
        )

    @task
    def conduct_interview(self) -> Task:
        return Task(
            config=self.tasks_config['conduct_interview'],
            output_pydantic=InterviewerUpdate,
            agent=self.interviewer(),
        )

    @agent
    def assistive_technical_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['assistive_technical_specialist'],
            allow_delegation=True,
            verbose=False,
            llm=settings.llm
        )

    @agent
    def assistive_company_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['assistive_company_manager'],
            allow_delegation=False,
            verbose=False,
            llm=settings.llm
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False
        )


def kickoff_interview(crew, state: InterviewState) -> InterviewerUpdate:
    try:
        inputs = {**conduct_interview_input(state), **formulate_technical_question_input(state)}
        res = crew.crew().kickoff(inputs=inputs)
        return res.pydantic
    except:
        return kickoff_interview(crew, state)

def conduct_interview_input(state: InterviewState) -> Dict:
    return dict(
        current_question=state.current_question or "Вопрос еще не задан",
        moderator_context=(
            f"Категория: {state.moderator_context.category}, "
            f"Рекомендация: {state.moderator_context.recommendation}"
        ),
        evaluator_context=(
            f"Есть оценка: {state.evaluator_context.has_info_about_answer}, "
            f"Оценка: {state.evaluator_context.score:.2f}, "
            f"Корректировка: {state.evaluator_context.should_correct_user}"
        ),
        strategist_context=(
            f"Действие: {state.strategist_context.next_action}, "
            f"Сложность: {state.strategist_context.current_difficulty}, "
            f"Тема: {state.strategist_context.next_topic}"
        ),
        candidate_answer=state.candidate_answer
    )


def formulate_technical_question_input(state: InterviewState) -> Dict:
    return dict(
        topic=state.strategist_context.next_topic or state.interview_topic,
        difficulty=state.strategist_context.current_difficulty,
        target_grade=state.candidate.target_grade,
        previous_questions="\n".join(i.model_dump_json() for i in state.history[-3:]) if state.history else "Предыдущих вопросов не было",
    )
