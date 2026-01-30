#!/usr/bin/env python
import time
from datetime import datetime

from crewai.flow.flow import Flow, listen, start, and_, router, or_

from interview.crews.moderation_crew.crew import ModerationCrew
from interview.interview_log import InterviewLogger
from state import *


class InterviewFlow(Flow[InterviewState]):
    def __init__(self):
        super().__init__()
        self.logger: Optional[InterviewLogger] = None

    def ui_out(self, text: str):
        text += "\n"
        self.logger.on_interviewer(text)
        print(text)

    def ui_in(self, prompt: str = ""):
        txt = input(prompt + "\n> ")
        return txt.strip()

    @start()
    def initialize_interview(self):
        """Set up the interview base info"""
        # name = self.ui_in("Имя: ")
        # position = self.ui_in("Позиция: ")
        # grade_choice = self.ui_in("Целевой грейд (junior, middle, senior): ").upper()
        # grade = GradeLevel.__dict__.get(grade_choice, GradeLevel.JUNIOR)
        # experience = self.ui_in("Опыт работы кратко: ")
        # self.state.participant = CandidateInfo(
        #     name=name,
        #     position=position,
        #     target_grade=grade,
        #     experience=experience
        # )
        candidate = CandidateInfo(
            name="петр",
            position="senior enterprise python developer",
            target_grade=GradeLevel.SENIOR,
            experience="много опыта"
        )
        self.state.candidate = candidate
        self.state.is_initialized = True
        self.state.interview_topic = f"Собеседование на позицию {candidate.position} ({candidate.target_grade.value})"
        self.logger = InterviewLogger(candidate.name)

        self.ui_out(f"\nНачинаем интервью. Для досрочного завершения можно попросить остановить интервью.")
        return "initialized"

    @listen(or_(initialize_interview, "continue_interview"))
    def prepare_question(self, _):
        """Propose next question"""
        print("Thinking of question...")
        question = f"""Q?"""
        self.state.current_question = question

        self.logger.next()
        return self.state.current_question

    @listen(or_(prepare_question, "repeat_question"))
    def ask_question(self):
        """Ask prepared question"""
        q = self.state.current_question
        self.ui_out(f"\n[Interviewer]: {q}\n")
        self.logger.on_interviewer(q)
        return self.state.current_question

    @listen(ask_question)
    def get_candidate_answer(self, _):
        """Get response from candidate"""
        response = self.ui_in()
        self.logger.on_user(response)
        self.state.candidate_answer = response
        return response

    @router(get_candidate_answer)
    def moderate_input(self, candidate_text):
        """Apply input moderation and minimal intention classification"""
        moderation = ModerationCrew().crew().kickoff(
            inputs=dict(
                interview_topic=self.state.interview_topic,
                candidate_message=candidate_text
            )).pydantic
        category = moderation.category
        if category == GuardCategory.ILLEGAL:
            self.ui_out(f"Пожалуйста, придерживайтесь темы интервью и правил общения.")
            return "repeat_question"
        elif category == GuardCategory.IRRELEVANT:
            self.ui_out(f"Ваш ответ не связан с вопросом интервью.\nДавайте вернемся к вопросу\n")
            return "repeat_question"
        elif category == GuardCategory.INFO:
            return "mod_handle_info"
        elif category == GuardCategory.RELEVANT:
            return "mod_handle_relevant"
        else:
            self.ui_out(f"Завершаем интервью")
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
        self.ui_out(f"Переход к следующему вопросу")
        return 'step done'

    def finalize_interview(self, _):
        """End interview"""
        self.ui_out(f"ИНТЕРВЬЮ ЗАВЕРШЕНО")
        with open(f"interview_log.{datetime.now().timestamp()}.json", "w") as f:
            f.write(self.logger.export())
        return "completed"


if __name__ == "__main__":
    InterviewFlow().kickoff()
