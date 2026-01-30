from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


# class GradeLevel(str, Enum):
#     JUNIOR = "Junior"
#     MIDDLE = "Middle"
#     SENIOR = "Senior"
#
#
# class HiringDecision(str, Enum):
#     NO_HIRE = "No Hire"
#     HIRE = "Hire"
#     STRONG_HIRE = "Strong Hire"
#
#
# class ParticipantInfo(BaseModel):
#     name: str = ""
#     position: str = ""
#     target_grade: GradeLevel = GradeLevel.JUNIOR
#     experience: str = ""
#

# class TopicCoverage(BaseModel):
#     topic: str
#     asked: bool = False
#     score: float = 0.0
#     difficulty: str = "easy"  # easy, medium, hard
#
#
# class TurnAnalysis(BaseModel):
#     turn_id: int
#     technical_accuracy: float = 0.0
#     completeness: float = 0.0
#     confidence_level: str = "medium"
#     clarity: float = 0.0
#     is_off_topic: bool = False
#     is_hallucination: bool = False
#     detected_issues: List[str] = []
#     knowledge_gaps: List[str] = []
#     correct_answers: Dict[str, str] = {}
#
#
# class Turn(BaseModel):
#     turn_id: int
#     agent_visible_message: str
#     user_message: str = ""
#     internal_thoughts: str = ""
#     timestamp: datetime = Field(default_factory=datetime.now)
#
#
# class SoftSkillsScore(BaseModel):
#     clarity: float = 0.0
#     honesty: float = 0.0
#     engagement: float = 0.0
#
#
# class FinalFeedback(BaseModel):
#     grade: GradeLevel
#     hiring_recommendation: HiringDecision
#     confidence_score: float  # 0-100
#
#     confirmed_skills: List[str] = []
#     knowledge_gaps: Dict[str, str] = {}  # topic -> correct answer
#
#     soft_skills: SoftSkillsScore = SoftSkillsScore()
#
#     topics_to_study: List[str] = []
#     recommended_resources: Dict[str, str] = {}
#     overall_summary: str = ""

#
# class ModerationResult(BaseModel):
#     reason: float
#     category: Literal["pass", "redirect", "correct"]
#
# class InterviewState(BaseModel):
#     participant: ParticipantInfo = ParticipantInfo()
#     completed: bool = False
#     interrupted: bool = False
#     current_user_input: str = ""
#
#
#     class Config:
#         use_enum_values = True


class GradeLevel(str, Enum):
    """Грейд"""
    INTERN = "intern"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"


class CandidateInfo(BaseModel):
    """Информация о кандидате"""
    name: str = Field(default="", description="Имя кандидата")
    position: str = Field(default="", description="Вакансия")
    target_grade: GradeLevel = Field(default=GradeLevel.JUNIOR, description="Целевой грейд")
    experience: str = Field(default="", description="Опыт работы")


class GuardCategory(str, Enum):
    """Категории классификатора сообщений"""
    ILLEGAL = "illegal"
    IRRELEVANT = "irrelevant"
    END = "end"
    INFO = "info"
    RELEVANT = "relevant"
    ERROR = "error"


class GuardClassificationResult(BaseModel):
    """Результат классификации сообщения по безопасности"""
    category: GuardCategory
    reason: str
    recommendation: str


class InterviewEvent(BaseModel):
    """События в процессе интервью"""
    event_type: str
    data: dict
    timestamp: Optional[str] = None


class InterviewState(BaseModel):
    """Состояние интервью"""
    candidate: Optional[CandidateInfo] = None

    interview_topic: str = ""

    current_question: str = ""
    candidate_answer: str = ""
    input_classification: Optional[GuardClassificationResult] = None

    conversation_history: List[dict] = Field(default_factory=list)
    question_count: int = 0

    is_initialized: bool = False
    is_active: bool = True
    is_interrupted: bool = False

    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True
