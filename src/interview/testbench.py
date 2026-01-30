import sys
from typing import Callable

import feedback
from crewai import Flow
from crewai.flow import HumanFeedbackProvider, HumanFeedbackPending, PendingFeedbackContext

from interview.state import CandidateInfo, GradeLevel
from interview.testagent2 import TestCandidateAgent
# from interview.testagent import TestCandidateAgent


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

        result = self.qa_fun(self.pending_query)

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

    if len(sys.argv) > 1:
        sc = open(sys.argv[-1]).read()
    else:
        sc = open("tb_scenario/m4.list").read()

    tester = TestCandidateAgent(CandidateInfo(
        name="Петр",
        position="Python developer",
        target_grade=GradeLevel.SENIOR,
        experience="много опыта в банковской сфере"
    ), sc)
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
