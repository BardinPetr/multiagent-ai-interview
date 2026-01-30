from typing import List, Dict

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from interview.state import InterviewState, StrategistContext, HistoryItem


@CrewBase
class DirectionCrew:
    """Crew for analyzing next steps of interview"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def interview_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['interview_strategist'],
            verbose=False
        )

    @agent
    def skills_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['skills_analyzer'],
            verbose=False
        )

    """"""

    @task
    def analyze_interview_progress(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_interview_progress'],
            agent=self.skills_analyzer()
        )

    @task
    def determine_next_strategy(self) -> Task:
        return Task(
            config=self.tasks_config['determine_next_strategy'],
            agent=self.interview_strategist(),
            context=[self.analyze_interview_progress()],
            output_pydantic=StrategistContext
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


def kickoff_direction(crew, state: InterviewState) -> StrategistContext:
    # try:
    inputs = evaluate_direction_input(state)
    res = crew.crew().kickoff(inputs=inputs)
    return res.pydantic
    # except:
    #     return StrategistContext(next_topic="continue")


def evaluate_direction_input(state: InterviewState) -> Dict:
    return dict(
        candidate_info=state.candidate.model_dump_json(),
        target_grade=state.candidate.target_grade,
        position=state.candidate.position,
        hard_skills_scores=', '.join([i.model_dump_json() for i in state.hards_by_topic.values()]),
        soft_skills_scores=state.softs.model_dump_json(),
        question_count=state.question_count,
        current_difficulty=state.strategist_context.current_difficulty,
        evaluator_context=state.evaluator_context.model_dump_json(),
        recent_history='\n '.join(i.model_dump_json() for i in state.history),
        current_topic=state.current_topic.model_dump_json(),
        topic_question_count=state.current_topic.asked_cnt,
        next_topic=state.strategist_context.next_topic or state.interview_topic,
        next_difficulty=state.strategist_context.current_difficulty,
    )
