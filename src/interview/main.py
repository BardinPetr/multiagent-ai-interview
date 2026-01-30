#!/usr/bin/env python
from datetime import datetime

from crewai.flow import persist
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.flow.human_feedback import human_feedback
from loguru import logger

import feedback
import interview_log
from interview.crews.direction_crew.crew import kickoff_direction, DirectionCrew
from interview.crews.evaluation_crew.crew import kickoff_qa_evaluation, EvaluationCrew
from interview.crews.final_crew.crew import kickoff_final, FinalCrew
from interview.crews.info_collector_crew.crew import InfoCollectorCrew
from interview.crews.interview_runtime_crew.crew import InterviewRuntimeCrew, kickoff_interview
from interview.crews.moderation_crew.crew import ModerationCrew
from state import *

log = interview_log.ilogger


@persist()
class InterviewFlow(Flow[InterviewState]):

    def __init__(self, persistence=None):
        super().__init__(persistence=persistence)

    # @start()
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
        info = InfoCollectorCrew().crew().kickoff(
            inputs=dict(
                candidate_summary=self.state.candidate.model_dump_json(),
                user_response=prev_user_input,
            )
        ).pydantic
        self.state.candidate = info.updated_info
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
        return self.prepare_question(None)

    """
    2 этап - интервью
    """

    @start()
    def initn(self):
        self.state.candidate = CandidateInfo(name="test", position="developer", target_grade=GradeLevel.SENIOR,
                                             experience="total")
        return ""

    @listen(or_("continue_interview", initn))
    def prepare_question(self, _):
        """Propose next question"""
        logger.info("[MAIN] prepare_question")
        result = kickoff_interview(InterviewRuntimeCrew(), self.state)
        logger.info(f"[MAIN] interviewer output {result}")
        if result.should_end:
            self.state.is_active = False
        self.state.current_question = result.user_message
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
        try:
            moderation = ModerationCrew().crew().kickoff(
                inputs=dict(
                    interview_topic=self.state.interview_topic,
                    interviewer_message=self.state.current_question,
                    candidate_message=candidate_text
                )).pydantic
        except:
            self.state.moderator_context = GuardClassificationResult()
            return "continue_interview"

        self.state.moderator_context = moderation
        category = moderation.category

        if category in {GuardCategory.ILLEGAL, GuardCategory.IRRELEVANT}:
            logger.warning(f"[GUARD] {category}: {candidate_text[:20]}")
            return "continue_interview"
        elif category == GuardCategory.INFO:
            logger.warning(f"[GUARD] question from candidate: {candidate_text[:20]}")
            return "continue_interview"
        elif category == GuardCategory.RELEVANT:
            return "mod_handle_relevant"
        elif category == GuardCategory.END or not self.state.is_active:
            self.state.is_active = False
            self.state.is_interrupted = True
            return self.finalize_interview(None)

    @listen("mod_handle_relevant")
    def handle_relevant(self, _):
        """Обработка релевантных ответов"""
        logger.info(f"[MAIN] continua analyze QA")
        result = kickoff_qa_evaluation(EvaluationCrew(), self.state)
        self.state.evaluator_context = result
        if t := self.state.hards_by_topic.get(result.topic.lower(), None):
            t.asked_cnt += 1
            t.score += result.score
        else:
            self.state.hards_by_topic[result.topic] = HardSkillScore(topic=result.topic, score=result.score,
                                                                     asked_cnt=1)
        if result.softskills:
            self.state.softs.update(result.softskills)
        logger.info(f"[MAIN] analysis output score={result.score} {result.softskills}")
        return "answer"

    @listen(handle_relevant)
    def qa_complete(self, _):
        logger.info(f"[MAIN] strategy...")
        result = kickoff_direction(DirectionCrew(), self.state)
        logger.info(f"[MAIN] output {result}")
        self.state.strategist_context = result
        next_topic = result.next_topic.lower()
        if self.state.current_topic.topic != next_topic:
            self.state.current_topic = HardSkillScore(topic=next_topic)
        if next_topic not in self.state.hards_by_topic:
            self.state.hards_by_topic[next_topic] = HardSkillScore(topic=next_topic)
        self.state.question_count += 1
        return "ok"

    @listen(or_(qa_complete))
    def continue_interview(self, _):
        """Continue interview"""
        if not self.state.is_active:
            return self.finalize_interview(None)
        return 'step done'

    @human_feedback(
        message="Ознакомьтесь с результатами интервью: ",
        provider=feedback.get_feedback_provider()
    )
    def finalize_interview(self, _):
        """End interview"""
        result = kickoff_final(FinalCrew(), self.state)
        log.data.final_feedback = result
        with open(f"logs/interview_log.{datetime.now().timestamp()}.json", "w") as f:
            f.write(log.export())
        with open(f"logs/interview_out.{datetime.now().timestamp()}.md", "w") as f:
            f.write(result)
        return result


if __name__ == "__main__":
    InterviewFlow().kickoff()
