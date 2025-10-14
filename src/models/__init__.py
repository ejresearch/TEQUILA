"""Pydantic schemas for TEQUILA curriculum system."""

# Week-level schemas
from .schemas_week import (
    WeekMetadata,
    Objective,
    VocabularyItem,
    Chant,
    DaySession,
    Assessment,
    SpiralLinks,
    MisconceptionItem,
    GenerationProvenance,
    WeekSpec,
)

# Day-level schemas
from .schemas_day import (
    DayMetadata,
    LessonStep,
    BehaviorProfile,
    DayObjectives,
    DaySpiralLinks,
    DayDocument,
)

# Flint field schemas
from .schemas_flint import (
    FlintBundle,
)

# Role context schemas
from .schemas_role import (
    Identity,
    StudentProfile,
    DailyCycle,
    ReinforcementMethod,
    FeedbackStyle,
    SuccessCriteria,
    KnowledgeRecycling,
    RoleContext,
)

__all__ = [
    # Week
    "WeekMetadata",
    "Objective",
    "VocabularyItem",
    "Chant",
    "DaySession",
    "Assessment",
    "SpiralLinks",
    "MisconceptionItem",
    "GenerationProvenance",
    "WeekSpec",
    # Day
    "DayMetadata",
    "LessonStep",
    "BehaviorProfile",
    "DayObjectives",
    "DaySpiralLinks",
    "DayDocument",
    # Flint
    "FlintBundle",
    # Role
    "Identity",
    "StudentProfile",
    "DailyCycle",
    "ReinforcementMethod",
    "FeedbackStyle",
    "SuccessCriteria",
    "KnowledgeRecycling",
    "RoleContext",
]
