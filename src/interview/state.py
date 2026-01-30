from enum import Enum
from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class GradeLevel(str, Enum):
    """Грейд"""
    INTERN = "intern"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"


class CandidateInfo(BaseModel):
    """Информация о кандидате"""
    name: Optional[str] = Field(default=None, description="Имя кандидата")
    position: Optional[str] = Field(default=None, description="Вакансия")
    target_grade: Optional[GradeLevel] = Field(default=None, description="Целевой грейд")
    experience: Optional[str] = Field(default=None, description="Опыт работы")


class InfoCollectionResult(BaseModel):
    """Результат предварительного сбора информации"""
    is_complete: bool = Field(default=False, description="Вся ли необходимая информация собрана")
    next_question: Optional[str] = Field(default=None, description="Следующий вопрос для пользователя")
    updated_info: CandidateInfo = Field(default_factory=CandidateInfo, description="Обновленная информация о кандидате")


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
    category: GuardCategory = GuardCategory.RELEVANT
    reason: str = ""
    recommendation: str = ""
    thoughts: str = ""


class HardSkillScore(BaseModel):
    """Результаты по каждой из тем, требуемых на позицию"""
    topic: str
    asked_cnt: int = 0
    score: float = 0.0  # -1.0 (absolute incomprehension) to +1.0 (ideal knowledge)


class SoftSkillScores(BaseModel):
    """Анализ по софтскилам чисто исходя из речи"""
    clarity: float = Field(
        0.0,
        ge=-1.0, le=1.0,
        description="Четкость и ясность изложения мысли. 1.0 - кристально ясное изложение, -1.0 - хаотичное непонятное изложение")
    honesty: float = Field(
        0.0,
        ge=-1.0, le=1.0,
        description="Честность и открытость в ответе. 1.0 - открыто признает пределы знаний, 0.0 - нейтрально, -1.0 - попытки скрыть незнание, выдумывание фактов"
    )
    engagement: float = Field(
        0.0,
        ge=-1.0, le=1.0,
        description="Вовлеченность и заинтересованность. 1.0 - высокая заинтересованность,0.0 - нейтральная вовлеченность, -1.0 - явная незаинтересованность"
    )
    thoughts: str = ""

    def update(self, other):
        return SoftSkillScores(clarity=self.clarity+other.clarity, honesty=self.honesty+self.honesty, engagement=self.engagement+other.engagement)

class Difficulty(str, Enum):
    """Категории сложности задач"""
    TALK = "talk"  # starting point
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTRA = "extra"


class StrategyAction(str, Enum):
    """Действия по велению стратега"""
    CONTINUE = "continue"
    FINISH = "finish"
    SWITCH_TOPIC = "switch_topic"
    DIFFICULTY_UP = "difficulty_up"
    DIFFICULTY_DOWN = "difficulty_down"


class StrategistContext(BaseModel):
    current_difficulty: Difficulty = Difficulty.TALK
    next_action: StrategyAction = StrategyAction.CONTINUE
    next_topic: str = ""
    thoughts: str = ""

    class Config:
        use_enum_values = True

class EvaluatorContext(BaseModel):
    has_info_about_answer: bool = False
    topic: str = ""
    score: float = Field(
        default=0.0, ge=-1.0, le=1.0,
        description="Итоговая оценка ответа. 1.0 - идеальный ответ, 0.5 - хороший ответ, 0.0 - средний/базовый ответ, -0.5 - слабый ответ, -1.0 - полное непонимание"
    )
    should_correct_user: bool = False
    valid_answer: Optional[str] = None
    softskills: Optional[SoftSkillScores] = None
    thoughts: str = Field(
        default="",
        description="Подробное обоснование итоговой оценки, включая анализ фактов, софтскиллов и корректировок"
    )

class InterviewerUpdate(BaseModel):
    should_end: bool = False
    user_message: str = ""
    thoughts: str = ""


class HistoryItem(BaseModel):
    question: Optional[str]
    answer: Optional[str]
    thoughts: Optional[List[str]]


class InterviewState(BaseModel):
    """Состояние интервью"""
    candidate: Optional[CandidateInfo] = None

    interview_topic: str = ""
    current_topic: HardSkillScore = HardSkillScore(topic="")

    hards_by_topic: Dict[str, HardSkillScore] = Field(default_factory=dict)
    softs: SoftSkillScores = SoftSkillScores()

    history: List[HistoryItem] = Field(default_factory=list)

    current_question: str = ""
    candidate_answer: str = ""

    question_count: int = 0

    is_initialized: bool = False
    is_active: bool = True
    is_interrupted: bool = False

    moderator_context: GuardClassificationResult = GuardClassificationResult()
    evaluator_context: EvaluatorContext = EvaluatorContext()
    strategist_context: StrategistContext = StrategistContext()

    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True
