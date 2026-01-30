import threading
from typing import List

from crewai import Agent
from crewai.events import BaseEventListener, TaskCompletedEvent
from pydantic import BaseModel
from rich.pretty import pretty_repr

from state import InterviewState, HistoryItem


class LogEntry(BaseModel):
    turn_id: int
    agent_visible_message: str = ""
    user_message: str = ""
    internal_thoughts: str = ""


class InterviewLog(BaseModel):
    participant_name: str = ""
    turns: List[LogEntry] = []
    final_feedback: str = ""


class InterviewLogger(BaseEventListener):
    def __init__(self):
        super().__init__()
        self.pending = []
        self.p_lock = threading.Lock()

    def flush(self) -> List[str]:
        with self.p_lock:
            data = self.pending.copy()
            self.pending.clear()
            return data

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_result(source: Agent, event: TaskCompletedEvent):
            out = event.output
            text = out.raw
            if out.pydantic and (thoughts := out.pydantic.dict().get('thoughts', None)):
                text = thoughts
            if out.json_dict and (thoughts := out.json_dict.get('thoughts', None)):
                text = thoughts
            with self.p_lock:
                self.pending.append(f"[{out.agent.strip()}]: {text}")


ilogger = InterviewLogger()


def l_new(state: InterviewState):
    l_flush_thoughts(state)
    state.history.append(HistoryItem(turn_id=len(state.history) + 1))


def l_update_texts(state: InterviewState):
    if not state.history: return
    last = state.history[-1]
    last.question = state.current_question
    last.answer = state.candidate_answer


def l_flush_thoughts(state: InterviewState):
    if not state.history: return
    state.history[-1].thoughts.extend(ilogger.flush())


def l_export(state: InterviewState, feedback: str) -> InterviewLog:
    l_flush_thoughts(state)
    return InterviewLog(
        participant_name=state.candidate.name,
        final_feedback=feedback,
        turns=[
            LogEntry(
                turn_id=i.turn_id,
                agent_visible_message=i.question,
                user_message=i.answer,
                internal_thoughts='\n'.join(i.thoughts)
            )
            for i in state.history
        ]
    )


def l_report(state_in: InterviewState) -> str:
    turns = "\n\n\n".join([
        f"""
## STEP {i.turn_id}

Q:

```
{i.question}
```

A:

```
{i.answer}
```

T:

{"".join(f"\n```\n{j}\n```\n" for j in i.thoughts)}

""" for i in state_in.history
    ])
    state = state_in.copy(exclude={'history'})
    return f"""
# Turns
{turns}

# Dump of context
```json
{pretty_repr(state)}
```
"""
