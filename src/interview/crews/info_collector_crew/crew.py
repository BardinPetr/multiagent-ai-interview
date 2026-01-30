from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, task, crew

from interview.state import InfoCollectionResult


@CrewBase
class InfoCollectorCrew:
    """Crew для сбора информации о кандидате"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def info_collector_agent(self) -> Agent:
        return Agent(
            role='Сборщик информации о кандидате',
            goal='Собрать полную информацию о кандидате для проведения технического интервью',
            backstory="""Вы - опытный HR-специалист с 10-летним стажем работы в IT-компаниях.
            Вы специализируетесь на первичном скрининге кандидатов и умеете эффективно собирать базовую информацию.
            Вы общаетесь на русском языке профессионально, но дружелюбно.

            Вашa задача - собрать следующую информацию:
            1. Имя кандидата (name) - как к нему/ней обращаться
            2. Желаемая позиция (position) - на какую должность претендует
            3. Целевой грейд (target_grade) - желаемый уровень: intern, junior, middle, senior, lead
            4. Опыт работы (experience) - краткое описание опыта в релевантной области

            Вы задаете вопросы последовательно и понятно, не перегружая кандидата.""",
            verbose=False,
            allow_delegation=False,
            llm='openrouter/google/gemini-2.5-flash'
        )

    @task
    def create_analysis_task(self) -> Task:
        """Создание задачи анализа собранной информации"""
        return Task(
            description="""
            Проанализируйте текущее состояние сбора информации о кандидате и определите следующий шаг.
            **Текущая информация о кандидате:**
            {candidate_summary}
            
            **Последний ответ пользователя:** {user_response}
            
            **Ваша задача:**
            1. Проанализируйте, какие поля уже заполнены, а какие нет
            2. Если есть новая информация в ответе пользователя, извлеките её и обновите соответствующие поля
            3. Определите, вся ли необходимая информация собрана
            4. Если информация не полная, сформулируйте конкретный, понятный вопрос на русском языке для получения недостающих данных
            5. Задавайте вопросы по одному полю за раз
            
            **Требования к полноте информации:**
            - Имя (name): не пустое
            - Позиция (position): не пустое  
            - Целевой грейд (target_grade): должен быть один из: intern, junior, middle, senior, lead
            - Опыт работы (experience): не пустое, хотя бы краткое описание
            
            **Примеры хороших вопросов:**
            - "Как мне можно к вам обращаться?"
            - "На какую позицию вы претендуете?"
            - "Какой грейд вас интересует? Выберите один из: intern, junior, middle, senior, lead"
            - "Расскажите, пожалуйста, кратко о вашем опыте работы в этой области"
            
            Не забудьте поздороваться в начале.
            
            в выводе данных может быть только JSON по pydantic модели, 
            ни в коем случае там не должно быть текстовых размышлений, комментариев и другой информации.
            общение с пользователем только через соответсвующее поле модели. 
            нельзя использовать markdown при выводе.
            """,
            expected_output="""информацию в соответствии с предоставленной pydantic моделью, ничего кроме данных модели не нужно выводить""",
            agent=self.info_collector_agent(),
            output_pydantic=InfoCollectionResult
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False
        )
