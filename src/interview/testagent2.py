from crewai import Agent, Task, Process, Crew

from interview.config.settings import settings
from interview.state import CandidateInfo


class TestCandidateAgent:
    def __init__(self, candidate: CandidateInfo, scenario: str):
        self.history = []
        agent = Agent(
            role=f'Актер, играющий кандидат на собеседовании',
            goal=f"""
                Твоя задача помочь организации проверить уровень сотрудников службы HR, 
                для этого ты должен сыграть роль кандидата на позицию,
                который пришел на собеседование и должен отвечать на вопросы рекрутера. 
                Ты должен работать по заданному сценарию. 
            """,
            backstory=f"""
                Далее тебе будет дана твоя история, которую надо будет отыгрывать:
                
                {scenario}

                Вначале тебя будут спрашивать о том кто ты и на какую позицию ты идешь, это нужно взять из сценария, 
                но это не относится к шагам, шаги сценария начинаются с первого заданного техничского вопроса.
                
                Отвечай так, как будто ты реально имеешь все опыт и навыки в соответствии со своим сценарием персонажа. 
                
                Кроме достижения цели получить вакансию, 
                тебе также необходимо отыграть все переданные сценарии строго по шагам
                Информация в сценарии приоритетнее всего!.
            """,
            allow_delegation=False,
            verbose=False,
            llm=settings.llm
        )

        task = Task(
            description=""
                        "ответить Вопрос от интервьюера: {question}"
                        ""
                        "учитывать историю общения: {history}",
            expected_output="Ответ на поставленный вопрос в том виде, в соответствии с тем, какую роль ты играешь, "
                            "но ни в коем случае не выдавай себя что ты актер."
                            "Сохраняй свои ответы краткими, пару предложений, не больше.",
            agent=agent
        )

        self.crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )

    def answer(self, question: str) -> str:
        print(f"[BOT] Q: {question}")
        res = self.crew.kickoff(inputs=dict(question=question, history='\n'.join(self.history))).raw
        print(f"[BOT] A: {res}")
        self.history.append(f"===\nQ: {question}\nA: {res}===")
        return res

