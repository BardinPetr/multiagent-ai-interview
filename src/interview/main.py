#!/usr/bin/env python
from datetime import datetime

from crewai.flow import persist
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.flow.human_feedback import human_feedback

import feedback
import interview_log
from interview.crews.info_collector import InfoCollectorCrew
from interview.crews.moderation_crew.crew import ModerationCrew
from state import *

from loguru import logger

log = interview_log.ilogger


@persist()
class InterviewFlow(Flow[InterviewState]):

    def __init__(self, persistence=None):
        super().__init__(persistence=persistence)

    @start()
    def initialize_interview(self):
        """Set up the interview base info"""
        self.state.candidate = CandidateInfo()
        return ""

    """
    1 этап - сбор данныъ о человеке
    """

    @listen("initialize_interview")
    def collect_info(self, prev_user_input):
        logger.info("[MAIN] collect_info")
        # noinspection PyTypeChecker
        info: InfoCollectionResult = InfoCollectorCrew().crew().kickoff(
            inputs=dict(
                candidate_summary=self.state.candidate.model_dump_json(),
                user_response=prev_user_input,
            )
        ).pydantic
        self.state.candidate = CandidateInfo(**info.updated_info)
        if info.is_complete:
            self.state.is_initialized = True
            self.state.interview_topic = f"Собеседование на позицию {self.state.candidate.position} ({self.state.candidate.target_grade.value})"
            return self.collect_info_done()
        else:
            return self.collect_info_rq(info.next_question)

    @human_feedback(
        message="Answer question: ",
        provider=feedback.get_feedback_provider()
    )
    def collect_info_rq(self, query):
        return query

    @listen(collect_info_rq)
    def collect_info_rs(self, response):
        return self.collect_info(response.feedback)

    def collect_info_done(self):
        logger.info(f"[MAIN] collect_info done {self.state.candidate}")
        return "collected"

    """
    2 этап - интервью
    """

    @listen(or_(collect_info_done, "continue_interview"))
    def prepare_question(self, _):
        """Propose next question"""
        print("Thinking of question...")
        question = f"""quo vadis?"""
        self.state.current_question = question
        return self.state.current_question

    @listen(or_(prepare_question, "repeat_question"))
    @human_feedback(
        message="Answer question: ",
        provider=feedback.get_feedback_provider()
    )
    def ask_question(self):
        """Ask prepared question"""
        q = self.state.current_question
        log.next()
        log.on_interviewer(q)
        return self.state.current_question

    @listen(ask_question)
    def get_candidate_answer(self, human_result):
        """Get response from candidate"""
        text = human_result.feedback
        log.on_user(text)
        self.state.candidate_answer = text
        return text

    @router(get_candidate_answer)
    def moderate_input(self, candidate_text):
        """Apply input moderation and minimal intention classification"""
        moderation = ModerationCrew().crew().kickoff(
            inputs=dict(
                interview_topic=self.state.interview_topic,
                candidate_message=candidate_text
            )).pydantic
        category = moderation.category
        print(f"[MODERATION] {category.name}")
        if category == GuardCategory.ILLEGAL:
            # self.ui_out(f"Пожалуйста, придерживайтесь темы интервью и правил общения.")
            return "repeat_question"
        elif category == GuardCategory.IRRELEVANT:
            # self.ui_out(f"Ваш ответ не связан с вопросом интервью.\nДавайте вернемся к вопросу\n")
            return "repeat_question"
        elif category == GuardCategory.INFO:
            return "mod_handle_info"
        elif category == GuardCategory.RELEVANT:
            return "mod_handle_relevant"
        else:
            self.state.is_active = False
            self.state.is_interrupted = True
            return self.finalize_interview(None)

    @listen("mod_handle_relevant")
    def handle_relevant(self, _):
        """Обработка релевантных ответов"""
        print(f"!РЕЛЕВАНТНЫЙ ОТВЕТ")
        return "answer"

    @listen(handle_relevant)
    def qa_complete(self, _):
        print("!qa_complete")
        return "ok"

    @listen("mod_handle_info")
    def handle_info(self, _):
        """Обработка вопросов о компании"""
        print("INFO")
        return "info"

    @listen(or_(qa_complete, handle_info))
    def continue_interview(self, _):
        """Continue interview"""
        if not self.state.is_active:
            return self.finalize_interview(None)
        return 'step done'

    def finalize_interview(self, _):
        """End interview"""
        with open(f"logs/interview_log.{datetime.now().timestamp()}.json", "w") as f:
            f.write(log.export())
        return "completed"


if __name__ == "__main__":
    InterviewFlow().kickoff()
