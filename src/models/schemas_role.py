"""Pydantic schemas for Sparky role context (AI tutor personality)."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Identity(BaseModel):
    """Sparky's character and teaching philosophy."""
    persona: str = Field(..., min_length=50, description="Who Sparky is as a teacher")
    teaching_philosophy: str = Field(..., min_length=50, description="Educational approach")
    faith_integration: Optional[str] = Field(None, description="How faith is woven into lessons")


class StudentProfile(BaseModel):
    """Target audience characteristics."""
    age_range: str = Field(..., description="Student age range")
    prior_knowledge: List[str] = Field(..., min_items=1, description="What students already know")
    learning_style: str = Field(..., description="How students learn best")
    attention_span: Optional[int] = Field(None, ge=15, le=60, description="Expected attention span in minutes")


class DailyCycle(BaseModel):
    """Typical lesson structure."""
    opening: str = Field(..., description="How lessons begin")
    core_activities: List[str] = Field(..., min_items=2, description="Main lesson components")
    closure: str = Field(..., description="How lessons end")
    duration_minutes: int = Field(45, ge=30, le=90, description="Typical lesson length")


class ReinforcementMethod(BaseModel):
    """How Sparky encourages and motivates."""
    positive_feedback: List[str] = Field(..., min_items=2, description="Types of encouragement")
    struggle_support: str = Field(..., description="How Sparky helps struggling students")
    celebration_style: str = Field(..., description="How success is celebrated")


class FeedbackStyle(BaseModel):
    """How Sparky corrects errors."""
    error_handling: str = Field(..., description="Approach to student mistakes")
    hint_progression: List[str] = Field(..., min_items=2, description="Steps from subtle to explicit hints")
    correction_tone: str = Field(..., description="Emotional tone when correcting")


class SuccessCriteria(BaseModel):
    """What mastery looks like."""
    knowledge_indicators: List[str] = Field(..., min_items=2, description="Signs of understanding")
    skill_indicators: List[str] = Field(..., min_items=2, description="Signs of skill mastery")
    readiness_for_next: str = Field(..., description="When students are ready to advance")


class KnowledgeRecycling(BaseModel):
    """Spiral learning approach."""
    review_frequency: str = Field(..., description="How often prior content returns")
    integration_strategy: str = Field(..., description="How old and new content combine")
    spiral_percentage: int = Field(..., ge=25, le=50, description="% of lesson reviewing prior content")


class RoleContext(BaseModel):
    """Complete Sparky role context definition."""
    identity: Identity
    student_profile: StudentProfile
    daily_cycle: DailyCycle
    reinforcement_method: ReinforcementMethod
    feedback_style: FeedbackStyle
    success_criteria: SuccessCriteria
    knowledge_recycling: KnowledgeRecycling
    generation_metadata: Optional[Dict[str, Any]] = Field(None, alias="__generation", description="Generation metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "identity": {
                    "persona": "A patient, encouraging Latin teacher who makes ancient languages accessible and exciting",
                    "teaching_philosophy": "Socratic questioning with joyful repetition and virtue-centered formation"
                },
                "knowledge_recycling": {
                    "review_frequency": "Daily",
                    "integration_strategy": "Begin each lesson with recall from previous 2-3 days",
                    "spiral_percentage": 30
                }
            }
        }
