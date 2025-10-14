"""Pydantic schemas for day-level curriculum structures."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime


class DayMetadata(BaseModel):
    """Metadata for a single day's lesson."""
    course: Literal["Latin A"] = "Latin A"
    week: int = Field(..., ge=1, le=36, description="Week number")
    day: int = Field(..., ge=1, le=4, description="Day number within week")
    title: str = Field(..., min_length=1, description="Lesson title")
    duration_minutes: int = Field(45, ge=15, le=120, description="Expected lesson duration")
    virtue: Optional[str] = Field(None, description="Virtue focus")
    faith_phrase: Optional[str] = Field(None, description="Faith phrase for the day")


class LessonStep(BaseModel):
    """Individual step in a lesson flow."""
    type: Literal[
        "recall", "introduction", "guided_practice",
        "independent_practice", "assessment", "transition",
        "greeting", "review", "chant", "derivatives",
        "agreement_drill", "dictation", "translation",
        "copywork", "faith_reflection", "closure"
    ]
    duration_minutes: int = Field(..., ge=1, le=60, description="Step duration")
    description: str = Field(..., min_length=10, description="What happens in this step")
    student_action: str = Field(..., min_length=5, description="Expected student behavior")
    teacher_notes: Optional[str] = Field(None, description="Notes for instructor")


class BehaviorProfile(BaseModel):
    """Sparky's pedagogical behavior profile."""
    tone: str = Field(..., description="Teaching tone (encouraging, socratic, etc.)")
    loop_behavior: str = Field(..., description="How Sparky handles repetition")
    hints_max: int = Field(3, ge=1, le=5, description="Max hints before revealing answer")
    wait_seconds: int = Field(5, ge=3, le=15, description="Wait time for student responses")
    encouragement_frequency: Optional[str] = Field(None, description="How often to encourage")


class DayObjectives(BaseModel):
    """Learning objectives for a single day."""
    primary: List[str] = Field(..., min_items=1, description="Main learning goals")
    spiral_review: List[str] = Field(default_factory=list, description="Review goals from prior weeks")


class DaySpiralLinks(BaseModel):
    """Day-specific spiral learning connections."""
    recycled_vocab: List[str] = Field(default_factory=list, description="Vocabulary from prior weeks")
    recycled_grammar: List[str] = Field(default_factory=list, description="Grammar from prior weeks")
    prior_day_concepts: List[str] = Field(default_factory=list, description="Concepts from previous day")
    prior_weeks: List[int] = Field(default_factory=list, description="Week dependencies")


class DayDocument(BaseModel):
    """Complete lesson plan document for a single day."""
    metadata: DayMetadata
    prior_knowledge_digest: str = Field(
        ...,
        min_length=120,
        max_length=300,
        description="Summary of prerequisite concepts"
    )
    yesterday_recap: str = Field(..., min_length=20, description="Brief review of previous lesson")
    spiral_links: DaySpiralLinks
    misconception_watchlist: List[str] = Field(
        default_factory=list,
        description="Common errors to watch for"
    )
    objectives: DayObjectives
    materials: List[str] = Field(..., min_items=1, description="Required resources")
    lesson_flow: List[LessonStep] = Field(..., min_items=3, description="Sequenced lesson steps")
    behavior: BehaviorProfile
    generation_metadata: Optional[Dict[str, Any]] = Field(None, alias="__generation", description="Generation metadata")

    @field_validator("lesson_flow")
    @classmethod
    def validate_spiral_opening(cls, v):
        """Ensure first 1-2 steps are recall/review."""
        if len(v) < 2:
            raise ValueError("Lesson flow must have at least 2 steps")

        first_two_types = [step.type for step in v[:2]]
        recall_types = {"recall", "review", "greeting"}

        # At least one of the first two steps should be recall/review
        if not any(t in recall_types for t in first_two_types):
            raise ValueError(
                "First 1-2 lesson steps must include recall/review of prior knowledge. "
                f"Found: {first_two_types}"
            )

        return v

    @field_validator("prior_knowledge_digest")
    @classmethod
    def validate_digest_length(cls, v):
        """Ensure prior knowledge digest is 120-200 words."""
        word_count = len(v.split())
        if word_count < 30:
            raise ValueError(f"Prior knowledge digest too short: {word_count} words (need 30+)")
        return v

    @field_validator("lesson_flow")
    @classmethod
    def validate_day4_assessment(cls, v, info):
        """Day 4 must include assessment step."""
        metadata = info.data.get("metadata")
        if metadata and hasattr(metadata, "day") and metadata.day == 4:
            has_assessment = any(step.type == "assessment" for step in v)
            if not has_assessment:
                raise ValueError(
                    "Day 4 must include an 'assessment' step type. "
                    "This enforces spiral learning review."
                )
        return v
