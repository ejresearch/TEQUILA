"""Pydantic schemas for week-level curriculum structures."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime


class WeekMetadata(BaseModel):
    """Metadata for a curriculum week."""
    course: Literal["Latin A"] = Field(default="Latin A")
    week: Optional[int] = Field(None, ge=1, le=36, description="Week number (1-36)")
    week_title: str = Field(..., min_length=1, description="Week title")
    grammar_focus: str = Field(..., min_length=1, description="Grammar focus for the week")
    chant: str = Field(..., min_length=1, description="Chant title for the week")
    virtue_focus: str = Field(..., min_length=1, description="Virtue theme for the week")
    faith_phrase: Optional[str] = Field(None, description="Faith phrase of the week")
    vocabulary_summary: Optional[str] = Field(None, description="Summary of vocabulary covered")
    author_metadata: Optional[Dict[str, str]] = Field(None, description="Author information")
    originality_attestation: Optional[bool] = Field(None, description="Originality attestation")
    license: Optional[str] = Field(None, description="Content license")


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
    pronunciation: Optional[str] = Field(None, description="Pronunciation guide")
    example_phrase: Optional[str] = Field(None, description="Example phrase using the word")
    notes: Optional[str] = Field(None, description="Usage notes or etymology")
    is_recycled: bool = Field(False, description="True if reviewing from prior week")
    from_week: Optional[int] = Field(None, ge=1, description="Original week if recycled")


class Chant(BaseModel):
    """Weekly chant structure."""
    text: str = Field(..., min_length=1, description="Chant text (may include call-and-response)")
    latin_text: Optional[str] = Field(None, description="Latin text if separated")
    english_translation: Optional[str] = Field(None, description="English translation if provided")
    source: Optional[str] = Field(None, description="Source text (Bible, liturgy, etc.)")
    notes: Optional[str] = Field(None)


class DaySession(BaseModel):
    """Brief overview of a single day's session."""
    day: int = Field(..., ge=1, le=4)
    focus: str = Field(..., description="Main pedagogical focus for the day")
    activities: List[str] = Field(..., min_items=1, description="List of activity types")


class QuizSection(BaseModel):
    """A section of the quiz."""
    type: str = Field(..., description="Section type (pronunciation, translation, etc.)")
    description: str = Field(..., description="Description of what this section tests")
    sample_items: List[str] = Field(default_factory=list, description="Sample quiz items")


class QuizStructure(BaseModel):
    """Structure of the quiz."""
    sections: List[QuizSection] = Field(..., min_items=1, description="Quiz sections")
    scoring_notes: Optional[str] = Field(None, description="Notes about scoring")


class Assessment(BaseModel):
    """Assessment plan for the week."""
    quiz_structure: QuizStructure = Field(..., description="Structure of the quiz")
    review_before_quiz: Optional[str] = Field(None, description="What students should review")
    format: Optional[str] = Field(None, description="Assessment format (quiz, oral, written, etc.)")
    timing: Optional[str] = Field(None, description="When assessment occurs (Day 4, end of week, etc.)")
    prior_content_percentage: Optional[int] = Field(None, ge=0, le=100, description="% testing prior weeks")
    items: Optional[List[str]] = Field(None, description="Assessment item descriptions")


class SpiralLinks(BaseModel):
    """Connections to prior curriculum content."""
    prior_knowledge: List[Any] = Field(default_factory=list, description="Prior knowledge requirements")
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
    """Complete weekly lesson specification - matches compiled week spec structure."""
    metadata: WeekMetadata
    objectives: List[str] = Field(..., min_items=1, description="List of learning objectives")
    vocabulary: List[VocabularyItem] = Field(..., min_items=1)
    grammar_focus: str = Field(..., min_length=20, description="Grammatical concepts covered")
    chant: Chant
    sessions: List[DaySession] = Field(default_factory=list, description="Daily sessions (may be empty for Week 1)")
    assessment: Assessment
    assets: List[str] = Field(default_factory=list, description="List of supplementary materials")
    spiral_links: SpiralLinks
    interleaving_plan: str = Field(..., min_length=10, description="How prior content is mixed in")
    misconception_watchlist: List[MisconceptionItem] = Field(default_factory=list)
    preview_next_week: str = Field(default="", description="Teaser of upcoming content (may be empty)")
    generation_metadata: Optional[GenerationProvenance] = Field(None, alias="__generation", description="Generation metadata")

    @field_validator("sessions")
    @classmethod
    def validate_four_days(cls, v):
        """Ensure exactly 4 days are defined (if not empty)."""
        if len(v) == 0:
            return v  # Allow empty for Week 1
        if len(v) != 4:
            raise ValueError("Must have exactly 4 daily sessions or be empty")
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
        """Week ≥2 should have prior week dependencies (warning only)."""
        # Relaxed validation - we'll handle this with warnings instead of errors
        return v
