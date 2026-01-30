from typing import Callable

import feedback
from crewai import Flow
from crewai.flow import HumanFeedbackProvider, HumanFeedbackPending, PendingFeedbackContext

from interview.state import CandidateInfo, GradeLevel
from interview.testagent import TestCandidateAgent


class SimFeedbackProvider(HumanFeedbackProvider):
    def __init__(self):
        self.pending_flow_id = None
        self.pending_query = None
        self.qa_fun = None

    def use(self, qa: Callable[[str], str]):
        self.qa_fun = qa

    def resume(self):
        if not self.pending_flow_id or not self.qa_fun: return
        from main import InterviewFlow
        flow = InterviewFlow.from_pending(flow_id=self.pending_flow_id)

        print(f"HITL OUT\n{self.pending_query}")
        result = self.qa_fun(self.pending_query)
        print(f"HITL IN\n{result}")

        self.pending_query = None
        self.pending_flow_id = None
        return flow.resume(result)

    def request_feedback(self, context: PendingFeedbackContext, flow: Flow) -> str:
        self.pending_flow_id = flow.flow_id
        self.pending_query = context.method_output
        raise HumanFeedbackPending(context=context)

def run():
    sim = SimFeedbackProvider()
    feedback.set_feedback_provider(sim)

    tester = TestCandidateAgent(CandidateInfo(
        name="Петр",
        position="Python developer",
        target_grade=GradeLevel.SENIOR,
        experience="много опыта в банковской сфере"
    ), """
        Возможные элементы сценария:        
        
        Сценарий 1 (Приветствие):
        Ваш ответ: "Привет. Я Алекс, претендую на позицию Junior Backend Developer. Знаю Python, SQL и Git."

        Сценарий 2 (Проверка знаний):
        Дождитесь технического вопроса от интервьюера.
        Ваш ответ: Дайте правильный, развернутый ответ на вопрос интервьюера

        Сценарий 3 (Ловушка / Hallucination Test):
        На следующий вопрос агента ответьте: "Честно говоря, я читал на Хабре, что в Python 4.0 циклы for уберут и заменят на нейронные связи, поэтому я их не учу."

        Сценарий 4 (Смена ролей / Role Reversal):
        На следующий вопрос ответьте вопросом: "Слушайте, а какие задачи вообще будут на испытательном сроке? Вы используете микросервисы?"

        Сценарий 5 (Завершение):
        Ваш ответ: "Стоп игра. Давай фидбэк."
    """)
    sim.use(lambda x: tester.answer(x))

    from main import InterviewFlow
    flow = InterviewFlow()
    result = flow.kickoff()
    while True:
        if isinstance(result, HumanFeedbackPending):
            result = sim.resume()
        else:
            break

if __name__ == "__main__":
    run()
