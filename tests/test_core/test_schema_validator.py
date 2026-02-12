"""
Tests for app.core.schema_validator — schema validation and frontmatter parsing.

All tests in this module are synchronous (no async/database dependency).
"""

import pytest

from app.core.schema_validator import SchemaValidator, parse_skill_md_frontmatter

SAMPLE_SKILL_MD = """---
name: test-skill
description: A test skill for validation
version: 0.0.1
---

# Test Skill

This skill is used for testing the skill manager functionality.

## Usage

Use this skill to test things and validate the schema correctly.
"""


@pytest.fixture
def validator() -> SchemaValidator:
    return SchemaValidator()


# ---------------------------------------------------------------------------
# validate_skill_name
# ---------------------------------------------------------------------------


class TestValidateSkillName:
    def test_valid_simple(self, validator: SchemaValidator):
        result = validator.validate_skill_name("my-skill")
        assert result.valid is True
        assert result.errors == []

    def test_valid_multi_segment(self, validator: SchemaValidator):
        result = validator.validate_skill_name("pdf-to-markdown")
        assert result.valid is True

    def test_valid_numeric(self, validator: SchemaValidator):
        result = validator.validate_skill_name("skill2pdf")
        assert result.valid is True

    def test_invalid_uppercase(self, validator: SchemaValidator):
        result = validator.validate_skill_name("Invalid Name")
        assert result.valid is False
        assert len(result.errors) > 0

    def test_invalid_single_char(self, validator: SchemaValidator):
        result = validator.validate_skill_name("a")
        assert result.valid is False

    def test_invalid_empty(self, validator: SchemaValidator):
        result = validator.validate_skill_name("")
        assert result.valid is False

    def test_invalid_starts_with_hyphen(self, validator: SchemaValidator):
        result = validator.validate_skill_name("-bad-name")
        assert result.valid is False

    def test_invalid_ends_with_hyphen(self, validator: SchemaValidator):
        result = validator.validate_skill_name("bad-name-")
        assert result.valid is False

    def test_invalid_consecutive_hyphens(self, validator: SchemaValidator):
        result = validator.validate_skill_name("bad--name")
        assert result.valid is False


# ---------------------------------------------------------------------------
# validate_version
# ---------------------------------------------------------------------------


class TestValidateVersion:
    def test_valid_simple(self, validator: SchemaValidator):
        result = validator.validate_version("1.2.3")
        assert result.valid is True

    def test_valid_zero(self, validator: SchemaValidator):
        result = validator.validate_version("0.0.1")
        assert result.valid is True

    def test_valid_prerelease(self, validator: SchemaValidator):
        result = validator.validate_version("1.0.0-beta.1")
        assert result.valid is True

    def test_valid_build_metadata(self, validator: SchemaValidator):
        result = validator.validate_version("1.0.0+build.123")
        assert result.valid is True

    def test_invalid_text(self, validator: SchemaValidator):
        result = validator.validate_version("abc")
        assert result.valid is False

    def test_invalid_empty(self, validator: SchemaValidator):
        result = validator.validate_version("")
        assert result.valid is False

    def test_invalid_partial(self, validator: SchemaValidator):
        result = validator.validate_version("1.2")
        assert result.valid is False


# ---------------------------------------------------------------------------
# validate_status
# ---------------------------------------------------------------------------


class TestValidateStatus:
    @pytest.mark.parametrize("status", ["active", "draft", "deprecated"])
    def test_valid(self, validator: SchemaValidator, status: str):
        result = validator.validate_status(status)
        assert result.valid is True

    def test_invalid_unknown(self, validator: SchemaValidator):
        result = validator.validate_status("unknown")
        assert result.valid is False

    def test_invalid_empty(self, validator: SchemaValidator):
        result = validator.validate_status("")
        assert result.valid is False

    def test_invalid_case_sensitive(self, validator: SchemaValidator):
        result = validator.validate_status("Active")
        assert result.valid is False


# ---------------------------------------------------------------------------
# validate_skill_md
# ---------------------------------------------------------------------------


class TestValidateSkillMd:
    def test_valid(self, validator: SchemaValidator):
        result = validator.validate_skill_md(SAMPLE_SKILL_MD)
        assert result.valid is True

    def test_empty(self, validator: SchemaValidator):
        result = validator.validate_skill_md("")
        assert result.valid is False
        assert any("required" in e.lower() for e in result.errors)

    def test_no_frontmatter_is_warning_not_error(self, validator: SchemaValidator):
        content = "# Just a heading\n\n" + "Some body text. " * 10
        result = validator.validate_skill_md(content)
        # Missing frontmatter is a warning, not an error, so still valid
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_invalid_yaml_frontmatter(self, validator: SchemaValidator):
        content = "---\n[bad yaml\n---\n\nBody text that is long enough to pass minimum length checks."
        result = validator.validate_skill_md(content)
        assert result.valid is False


# ---------------------------------------------------------------------------
# parse_skill_md_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_parse_valid(self):
        frontmatter, body = parse_skill_md_frontmatter(SAMPLE_SKILL_MD)
        assert isinstance(frontmatter, dict)
        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill for validation"
        assert frontmatter["version"] == "0.0.1"
        assert "# Test Skill" in body

    def test_parse_no_frontmatter(self):
        content = "# No frontmatter\nJust text."
        frontmatter, body = parse_skill_md_frontmatter(content)
        assert frontmatter == {}
        assert body == content

    def test_parse_invalid_yaml(self):
        content = "---\n[not valid yaml\n---\n\nBody."
        frontmatter, body = parse_skill_md_frontmatter(content)
        assert frontmatter == {}

    def test_parse_non_dict_yaml(self):
        content = "---\n- just a list\n---\n\nBody."
        frontmatter, body = parse_skill_md_frontmatter(content)
        assert frontmatter == {}
