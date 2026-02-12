"""
Schema Validator for Skill Registry.

Validates:
- Skill package structure
- JSON Schema compliance
- SKILL.md format
- manifest.json format
"""

import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import yaml
import jsonschema
from jsonschema import Draft202012Validator, ValidationError


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self) -> bool:
        return self.valid


class SchemaValidator:
    """Validates skill packages and their components."""

    # Required files in a skill package
    REQUIRED_FILES = ["SKILL.md"]

    # Valid file types
    FILE_TYPES = {"resource", "script", "test", "other"}

    # Valid skill statuses
    VALID_STATUSES = {"draft", "active", "deprecated"}

    # SemVer pattern
    SEMVER_PATTERN = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    # Skill name pattern (lowercase, hyphenated)
    NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def validate_skill_name(self, name: str) -> ValidationResult:
        """Validate a skill name."""
        errors = []
        warnings = []

        if not name:
            errors.append("Skill name is required")
        elif len(name) < 2:
            errors.append("Skill name must be at least 2 characters")
        elif len(name) > 128:
            errors.append("Skill name must be at most 128 characters")
        elif not self.NAME_PATTERN.match(name):
            errors.append(
                "Skill name must be lowercase, alphanumeric, and hyphen-separated"
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_version(self, version: str) -> ValidationResult:
        """Validate a SemVer version string."""
        errors = []
        warnings = []

        if not version:
            errors.append("Version is required")
        elif not self.SEMVER_PATTERN.match(version):
            errors.append(f"Invalid SemVer version: {version}")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_status(self, status: str) -> ValidationResult:
        """Validate a skill status."""
        errors = []
        warnings = []

        if status not in self.VALID_STATUSES:
            errors.append(
                f"Invalid status: {status}. Must be one of: {', '.join(self.VALID_STATUSES)}"
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_skill_md(self, content: str) -> ValidationResult:
        """
        Validate SKILL.md content.

        Expected format:
        ---
        name: skill-name
        description: Short description
        ---

        # Skill Title
        ...
        """
        errors = []
        warnings = []

        if not content:
            errors.append("SKILL.md content is required")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Check for YAML frontmatter
        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL
        )

        if not frontmatter_match:
            warnings.append("SKILL.md should have YAML frontmatter (---)")
        else:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                if not isinstance(frontmatter, dict):
                    errors.append("YAML frontmatter must be a dictionary")
                else:
                    if "name" not in frontmatter:
                        warnings.append("SKILL.md frontmatter should include 'name'")
                    if "description" not in frontmatter:
                        warnings.append(
                            "SKILL.md frontmatter should include 'description'"
                        )
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML frontmatter: {e}")

        # Check minimum content length
        body = content[frontmatter_match.end():] if frontmatter_match else content
        if len(body.strip()) < 50:
            warnings.append("SKILL.md content seems too short")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_json_schema(
        self, schema: Dict[str, Any], schema_name: str = "schema"
    ) -> ValidationResult:
        """Validate that a dict is a valid JSON Schema."""
        errors = []
        warnings = []

        if not schema:
            warnings.append(f"{schema_name} is empty")
            return ValidationResult(valid=True, errors=errors, warnings=warnings)

        try:
            # Check if it's a valid JSON Schema
            Draft202012Validator.check_schema(schema)
        except jsonschema.exceptions.SchemaError as e:
            errors.append(f"Invalid JSON Schema in {schema_name}: {e.message}")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_schema_json(
        self, schema_json: Dict[str, Any]
    ) -> ValidationResult:
        """Validate the schema.json structure."""
        errors = []
        warnings = []

        if not schema_json:
            warnings.append("schema.json is empty")
            return ValidationResult(valid=True, errors=errors, warnings=warnings)

        # Validate input schema if present
        if "input" in schema_json:
            result = self.validate_json_schema(schema_json["input"], "input schema")
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        # Validate output schema if present
        if "output" in schema_json:
            result = self.validate_json_schema(schema_json["output"], "output schema")
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_manifest(self, manifest: Dict[str, Any]) -> ValidationResult:
        """Validate manifest.json content."""
        errors = []
        warnings = []

        if not manifest:
            errors.append("manifest.json is required")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Required fields
        if "name" not in manifest:
            errors.append("manifest.json must include 'name'")
        else:
            name_result = self.validate_skill_name(manifest["name"])
            errors.extend(name_result.errors)

        if "version" not in manifest:
            errors.append("manifest.json must include 'version'")
        else:
            version_result = self.validate_version(manifest["version"])
            errors.extend(version_result.errors)

        if "description" not in manifest:
            warnings.append("manifest.json should include 'description'")

        # Optional fields validation
        if "tags" in manifest:
            if not isinstance(manifest["tags"], list):
                errors.append("manifest.json 'tags' must be an array")

        if "triggers" in manifest:
            if not isinstance(manifest["triggers"], list):
                errors.append("manifest.json 'triggers' must be an array")

        if "dependencies" in manifest:
            deps = manifest["dependencies"]
            if not isinstance(deps, dict):
                errors.append("manifest.json 'dependencies' must be an object")
            else:
                for key in ["mcp", "tools", "skills"]:
                    if key in deps and not isinstance(deps[key], list):
                        errors.append(f"manifest.json 'dependencies.{key}' must be an array")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_package(
        self,
        skill_md: Optional[str] = None,
        schema_json: Optional[Dict[str, Any]] = None,
        manifest_json: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate a complete skill package."""
        errors = []
        warnings = []

        # Validate SKILL.md
        if skill_md:
            result = self.validate_skill_md(skill_md)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        else:
            errors.append("SKILL.md is required")

        # Validate schema.json
        if schema_json:
            result = self.validate_schema_json(schema_json)
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        # Validate manifest.json
        if manifest_json:
            result = self.validate_manifest(manifest_json)
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_data_against_schema(
        self, data: Any, schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate data against a JSON Schema."""
        errors = []
        warnings = []

        if not schema:
            return ValidationResult(valid=True, errors=errors, warnings=warnings)

        try:
            validator = Draft202012Validator(schema)
            validation_errors = list(validator.iter_errors(data))

            for error in validation_errors:
                path = ".".join(str(p) for p in error.absolute_path)
                if path:
                    errors.append(f"Validation error at '{path}': {error.message}")
                else:
                    errors.append(f"Validation error: {error.message}")

        except Exception as e:
            errors.append(f"Schema validation failed: {str(e)}")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def compute_content_hash(content: bytes) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content).hexdigest()


def parse_skill_md_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse SKILL.md and extract frontmatter.

    Returns:
        Tuple of (frontmatter dict, body content)
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            frontmatter = {}
    except yaml.YAMLError:
        frontmatter = {}

    body = content[match.end():]
    return frontmatter, body


# Global validator instance
validator = SchemaValidator()
