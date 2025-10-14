"""Pydantic schemas for week-level curriculum structures."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime


class WeekMetadata(BaseModel):
    """Metadata for a curriculum week."""
    course: Literal["Latin A"] = "Latin A"
    week: int = Field(..., ge=1, le=36, description="Week number (1-36)")
    title: str = Field(..., min_length=1, description="Week title")
    virtue_focus: str = Field(..., min_length=1, description="Virtue theme for the week")
    faith_phrase: Optional[str] = Field(None, description="Faith phrase of the week")


class Objective(BaseModel):
    """Learning objective for the week."""
    id: str = Field(..., description="Unique objective ID (e.g., 'obj_w11_1')")
    description: str = Field(..., min_length=10, description="Objective description")
    category: Literal["vocabulary", "grammar", "translation", "culture", "faith"]


class VocabularyItem(BaseModel):
    """Vocabulary word entry."""
    latin: str = Field(..., min_length=1, description="Latin word")
    english: str = Field(..., min_length=1, description="English translation")
    part_of_speech: str = Field(..., description="Part of speech (noun, verb, adj, etc.)")
    notes: Optional[str] = Field(None, description="Usage notes or etymology")
    is_recycled: bool = Field(False, description="True if reviewing from prior week")
    from_week: Optional[int] = Field(None, ge=1, description="Original week if recycled")


class Chant(BaseModel):
    """Weekly chant structure."""
    latin_text: str = Field(..., min_length=1)
    english_translation: str = Field(..., min_length=1)
    source: Optional[str] = Field(None, description="Source text (Bible, liturgy, etc.)")
    notes: Optional[str] = Field(None)


class DaySession(BaseModel):
    """Brief overview of a single day's session."""
    day: int = Field(..., ge=1, le=4)
    focus: str = Field(..., description="Main pedagogical focus for the day")
    activities: List[str] = Field(..., min_items=1, description="List of activity types")


class Assessment(BaseModel):
    """Assessment plan for the week."""
    format: str = Field(..., description="Assessment format (quiz, oral, written, etc.)")
    timing: str = Field(..., description="When assessment occurs (Day 4, end of week, etc.)")
    prior_content_percentage: int = Field(..., ge=25, le=100, description="% testing prior weeks")
    items: List[str] = Field(..., min_items=1, description="Assessment item descriptions")


class SpiralLinks(BaseModel):
    """Connections to prior curriculum content."""
    prior_weeks_dependencies: List[int] = Field(default_factory=list, description="Required prior weeks")
    recycled_vocab: List[str] = Field(default_factory=list, description="Vocabulary from prior weeks")
    recycled_grammar: List[str] = Field(default_factory=list, description="Grammar from prior weeks")
    notes: Optional[str] = Field(None)


class MisconceptionItem(BaseModel):
    """Common student misconception to address."""
    concept: str = Field(..., description="The concept students struggle with")
    common_error: str = Field(..., description="Typical mistake students make")
    correction_strategy: str = Field(..., description="How to address the misconception")


class GenerationProvenance(BaseModel):
    """Metadata about how this content was generated."""
    provider: Literal["openai", "anthropic"]
    model: str
    created_at: datetime
    git_commit: Optional[str] = None
    tokens_prompt: Optional[int] = Field(None, ge=0)
    tokens_completion: Optional[int] = Field(None, ge=0)


class WeekSpec(BaseModel):
    """Complete weekly lesson specification."""
    metadata: WeekMetadata
    objectives: List[Objective] = Field(..., min_items=1)
    vocabulary: List[VocabularyItem] = Field(..., min_items=1)
    grammar_focus: str = Field(..., min_length=20, description="Grammatical concepts covered")
    chant: Chant
    sessions: List[DaySession] = Field(..., min_items=4, max_items=4, description="4 daily sessions")
    assessment: Assessment
    assets: List[str] = Field(default_factory=list, description="List of supplementary materials")
    spiral_links: SpiralLinks
    interleaving_plan: str = Field(..., min_length=50, description="How prior content is mixed in")
    misconception_watchlist: List[MisconceptionItem] = Field(default_factory=list)
    preview_next_week: str = Field(..., min_length=20, description="Teaser of upcoming content")
    generation_metadata: Optional[GenerationProvenance] = Field(None, alias="__generation", description="Generation metadata")

    @field_validator("sessions")
    @classmethod
    def validate_four_days(cls, v):
        """Ensure exactly 4 days are defined."""
        if len(v) != 4:
            raise ValueError("Must have exactly 4 daily sessions")
        days = [s.day for s in v]
        if sorted(days) != [1, 2, 3, 4]:
            raise ValueError("Sessions must cover days 1-4")
        return v

    @field_validator("vocabulary")
    @classmethod
    def validate_recycled_vocab(cls, v):
        """Ensure recycled vocab has from_week set."""
        for item in v:
            if item.is_recycled and item.from_week is None:
                raise ValueError(f"Recycled vocab '{item.latin}' must specify from_week")
        return v

    @field_validator("spiral_links")
    @classmethod
    def validate_spiral_dependencies(cls, v, info):
        """Week ≥2 must have prior week dependencies."""
        week = info.data.get("metadata", {}).week if hasattr(info.data.get("metadata"), "week") else None

        # If we can determine week number and it's ≥2, require dependencies
        if week and week >= 2:
            if not v.prior_weeks_dependencies or len(v.prior_weeks_dependencies) == 0:
                raise ValueError(
                    f"Week {week} must have prior_weeks_dependencies in spiral_links. "
                    "Spiral learning requires building on prior content."
                )
        return v
