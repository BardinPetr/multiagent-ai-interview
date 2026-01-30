from crewai import Agent, Task, Process, Crew

from interview.state import CandidateInfo


class TestCandidateAgent:
    def __init__(self, candidate: CandidateInfo, scenario: str):
        self.history = []
        agent = Agent(
            role=f'Актер, играющий кандидат на собеседовании на позицию {candidate.position}',
            goal=f"""
                Твоя задача помочь организации проверить уровень сотрудников службы HR, 
                для этого ты должен сыграть роль кандидата на позицию {candidate.target_grade} {candidate.position},
                который пришел на собеседование и должен отвечать на вопросы рекрутера. 
                Ты должен 
            """,
            backstory=f"""
                Твоя задача помочь организации проверить уровень сотрудников службы HR 
                и сыграть роль кандидата при приеме на работу. 
                Ты не должен спалиться: то есть рекрутер не должен смочь догадаться, 
                что ты не реальный кандидат, а подосланный актер для его проверки.
                
                Далее тебе будет дана твоя история, которую надо будет отыгрывать:
                
                Тебя зовут: {candidate.name}.
                Ты работал в направлении {candidate.position} и теперь меняешь работу.
                На очередном собеседовании ты хочешь получить оффер уровня {candidate.target_grade}.
                Твой опыт: 
                {candidate.experience}
                
                Отвечай так, как будто ты реально имеешь все опыт и навыки в соответствии со своим сценарием персонажа. 
                Сохраняй свои ответы краткими, пару предложений, не больше.
                
                Если диалог не развивается и интревьюер ведет себя странно, то попроси закончить интервью. 
                
                Кроме обычного диалога для достижения цели получить вакансию, 
                тебе также необходимо отыграть все сценарии их перечисленных ниже:
                Информация в сценарии приоритетнее всего!.
                
                {scenario}
            """,
            allow_delegation=False,
            verbose=False,
            llm="openrouter/google/gemini-2.5-flash"
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

