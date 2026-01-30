from typing import List

from crewai import Agent
from crewai.events import BaseEventListener, TaskCompletedEvent
from pydantic import BaseModel


class LogEntry(BaseModel):
    turn_id: int
    agent_visible_message: str = ""
    user_message: str = ""
    internal_thoughts: str = ""


class InterviewLog(BaseModel):
    participant_name: str
    turns: List[LogEntry] = []
    final_feedback: str = ""


class InterviewLogger(BaseEventListener):
    def __init__(self, participant_name: str):
        super().__init__()
        self.data = InterviewLog(participant_name=participant_name)

    def next(self):
        self.data.turns.append(LogEntry(turn_id=len(self.data.turns) + 1))

    def on_interviewer(self, question):
        if not self.data.turns: return
        self.data.turns[-1].agent_visible_message += question

    def on_user(self, answer):
        if not self.data.turns: return
        self.data.turns[-1].user_message = answer

    def on_internal(self, name, text):
        if not self.data.turns: return
        self.data.turns[-1].internal_thoughts += f"\n[{name}]: {text}\n------"

    def on_final(self, text):
        self.data.turns[-1].final_feedback = text

    def export(self) -> str:
        return self.data.model_dump_json(indent=2, ensure_ascii=False)

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_result(source: Agent, event: TaskCompletedEvent):
            out = event.output
            text = out.raw
            if out.pydantic and (reason := out.pydantic.dict().get('reason', None)):
                text = reason
            if out.json_dict and (reason := out.json_dict.get('reason', None)):
                text = reason
            self.on_internal(source.role, text)
