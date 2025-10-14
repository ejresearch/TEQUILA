"""Test suite for 7-field day architecture migration."""
import pytest
from pathlib import Path

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.storage import (
    detect_day_layout,
    get_day_fields,
    DAY_FIELDS,
    LEGACY_DAY_FIELDS
)
from src.cli.migrate_to_7field import derive_default_role_context


class TestLayoutDetection:
    """Test day layout detection (6-field vs 7-field)."""

    def test_day_fields_count(self):
        """7-field should have 7 fields, 6-field should have 6."""
        assert len(DAY_FIELDS) == 7
        assert len(LEGACY_DAY_FIELDS) == 6

    def test_role_context_in_7field(self):
        """04_role_context.json should be in 7-field DAY_FIELDS."""
        assert "04_role_context.json" in DAY_FIELDS

    def test_role_context_not_in_legacy(self):
        """04_role_context.json should NOT be in LEGACY_DAY_FIELDS."""
        assert "04_role_context.json" not in LEGACY_DAY_FIELDS


class TestRoleContextDefaults:
    """Test default role_context generation."""

    def test_derive_default_role_context_day1(self):
        """Should use 'introduction' focus for Day 1."""
        rc = derive_default_role_context(1, 1)
        assert rc["focus_mode"] == "introduction_and_exploration"
        assert rc["hints_enabled"] is True
        assert "__migration" in rc

    def test_derive_default_role_context_day2(self):
        """Should use 'practice' focus for Day 2."""
        rc = derive_default_role_context(1, 2)
        assert rc["focus_mode"] == "practice_and_reinforcement"

    def test_derive_default_role_context_day3(self):
        """Should use 'application' focus for Day 3."""
        rc = derive_default_role_context(1, 3)
        assert rc["focus_mode"] == "application_and_extension"

    def test_derive_default_role_context_day4(self):
        """Should use 'review_and_spiral' focus for Day 4."""
        rc = derive_default_role_context(3, 4)
        assert rc["focus_mode"] == "review_and_spiral"
        assert len(rc["spiral_emphasis"]) > 0  # Should reference prior week

    def test_derive_default_has_required_fields(self):
        """All required role_context fields should be present."""
        rc = derive_default_role_context(5, 2)
        required = ["sparky_role", "focus_mode", "hints_enabled", "spiral_emphasis", "encouragement_triggers"]
        for field in required:
            assert field in rc

    def test_derive_default_has_provenance(self):
        """Migration should include provenance metadata."""
        rc = derive_default_role_context(5, 2)
        assert "__migration" in rc
        assert "migrated_at" in rc["__migration"]
        assert "migration_script" in rc["__migration"]


class TestFieldMigrationMap:
    """Test field name migration mapping."""

    def test_guidelines_renaming(self):
        """04_guidelines should map to 05_guidelines."""
        from src.services.storage import FIELD_MIGRATION_MAP
        assert FIELD_MIGRATION_MAP["04_guidelines_for_sparky.md"] == "05_guidelines_for_sparky.md"

    def test_document_renaming(self):
        """05_document should map to 06_document."""
        from src.services.storage import FIELD_MIGRATION_MAP
        assert FIELD_MIGRATION_MAP["05_document_for_sparky.json"] == "06_document_for_sparky.json"

    def test_greeting_renaming(self):
        """06_greeting should map to 07_greeting."""
        from src.services.storage import FIELD_MIGRATION_MAP
        assert FIELD_MIGRATION_MAP["06_sparkys_greeting.txt"] == "07_sparkys_greeting.txt"


class TestSchemaChanges:
    """Test FlintBundle schema includes role_context."""

    def test_flint_bundle_has_role_context(self):
        """FlintBundle should have role_context field."""
        from src.models.schemas_flint import FlintBundle
        fields = FlintBundle.model_fields
        assert "role_context" in fields

    def test_role_context_is_optional(self):
        """role_context should be Optional (not required)."""
        from src.models.schemas_flint import FlintBundle
        # Create bundle without role_context - should not raise
        bundle = FlintBundle(
            class_name="Test",
            summary="A test summary with enough characters to meet minimum length requirement.",
            grade_level="3-5",
            guidelines_for_sparky="Test guidelines that meet the minimum length requirement for this field to be valid.",
            sparkys_greeting="Welcome students!"
        )
        assert bundle.role_context is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
