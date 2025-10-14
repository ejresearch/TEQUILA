"""Pydantic schemas for Flint field structures (day metadata fields)."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class FlintBundle(BaseModel):
    """
    The six Flint fields that make up a day's metadata.

    These fields provide context for the lesson builder system (Flint)
    and are separate from the detailed lesson plan (document_for_sparky).
    """
    class_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Short lesson title (e.g., 'Week 11 Day 1: Latin Nouns')"
    )

    summary: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="2-3 sentence overview of the lesson"
    )

    grade_level: str = Field(
        ...,
        pattern=r"^\d{1,2}-\d{1,2}$",
        description="Target grade range (e.g., '3-5', '6-8')"
    )

    guidelines_for_sparky: str = Field(
        ...,
        min_length=100,
        description="Markdown-formatted teaching notes and pedagogical guidance"
    )

    sparkys_greeting: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="1-2 sentence warm, encouraging greeting for students"
    )

    document_for_sparky: Optional[Dict[str, Any]] = Field(
        None,
        description="Complete lesson plan JSON (DayDocument schema)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "class_name": "Week 11 Day 1: First Declension Nouns",
                "summary": "Students will learn the nominative and accusative cases of first declension nouns. Focus on proper noun endings and their use in simple sentences.",
                "grade_level": "3-5",
                "guidelines_for_sparky": "# Teaching Notes\n\n- Use visual aids for noun endings\n- Practice with familiar vocabulary first\n- Emphasize sing-song chanting for memorization",
                "sparkys_greeting": "Welcome, young Latin scholars! Today we begin our journey into the beautiful world of Latin nouns."
            }
        }
