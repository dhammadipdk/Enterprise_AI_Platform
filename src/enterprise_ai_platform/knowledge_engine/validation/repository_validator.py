"""
Knowledge repository validator.
"""

from __future__ import annotations

from enterprise_ai_platform.knowledge_engine.models import (
    KnowledgeDomain,
    KnowledgeRepository,
)
from enterprise_ai_platform.knowledge_engine.validation.validation_issue import (
    ValidationIssue,
)
from enterprise_ai_platform.knowledge_engine.validation.validation_report import (
    ValidationReport,
)


class RepositoryValidator:
    """
    Validates the structural integrity of a KnowledgeRepository.
    """

    def validate(
        self,
        repository: KnowledgeRepository,
    ) -> ValidationReport:
        """
        Run all validation rules against a repository.
        """

        issues: list[ValidationIssue] = []

        issues.extend(self._check_repository_not_empty(repository))

        for domain in repository.domains:

            issues.extend(self._check_domain_not_empty(domain))

            issues.extend(self._check_no_duplicate_assets(domain))

            issues.extend(self._check_assets_exist_on_disk(domain))

            issues.extend(self._check_domain_has_documentation(domain))

        return ValidationReport(issues=issues)

    @staticmethod
    def _check_repository_not_empty(
        repository: KnowledgeRepository,
    ) -> list[ValidationIssue]:

        if repository.domains:
            return []

        return [
            ValidationIssue(
                severity="error",
                code="EMPTY_REPOSITORY",
                message="Repository contains no domains.",
            )
        ]

    @staticmethod
    def _check_domain_not_empty(
        domain: KnowledgeDomain,
    ) -> list[ValidationIssue]:

        if domain.assets:
            return []

        return [
            ValidationIssue(
                severity="error",
                code="EMPTY_DOMAIN",
                message=f"Domain '{domain.name}' contains no assets.",
                domain=domain.name,
            )
        ]

    @staticmethod
    def _check_no_duplicate_assets(
        domain: KnowledgeDomain,
    ) -> list[ValidationIssue]:

        seen: set[str] = set()

        duplicates: set[str] = set()

        for asset in domain.assets:

            if asset.name in seen:
                duplicates.add(asset.name)

            seen.add(asset.name)

        return [
            ValidationIssue(
                severity="error",
                code="DUPLICATE_ASSET_NAME",
                message=(
                    f"Domain '{domain.name}' has more than one asset "
                    f"named '{name}'."
                ),
                domain=domain.name,
                asset=name,
            )
            for name in sorted(duplicates)
        ]

    @staticmethod
    def _check_assets_exist_on_disk(
        domain: KnowledgeDomain,
    ) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []

        for asset in domain.assets:

            if asset.path.is_file():
                continue

            issues.append(
                ValidationIssue(
                    severity="error",
                    code="MISSING_ASSET_PATH",
                    message=(
                        f"Asset '{asset.name}' in domain '{domain.name}' "
                        f"does not exist at '{asset.path}'."
                    ),
                    domain=domain.name,
                    asset=asset.name,
                )
            )

        return issues

    @staticmethod
    def _check_domain_has_documentation(
        domain: KnowledgeDomain,
    ) -> list[ValidationIssue]:

        has_documentation = any(
            asset.asset_type == "documentation" for asset in domain.assets
        )

        if has_documentation:
            return []

        return [
            ValidationIssue(
                severity="warning",
                code="MISSING_DOCUMENTATION",
                message=(
                    f"Domain '{domain.name}' has no README / "
                    f"documentation asset."
                ),
                domain=domain.name,
            )
        ]