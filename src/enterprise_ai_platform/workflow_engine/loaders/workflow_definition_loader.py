"""
Workflow definition loader.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.workflow_engine.models import (
    RetryPolicy,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)


class WorkflowDefinitionLoader:
    """
    Builds a WorkflowDefinition from raw parsed data (a dict, matching
    the same shape used throughout this platform -- e.g. parsed YAML,
    exactly like PromptDefinitionLoader for the Prompt Engine).
    """

    def load(self, data: dict[str, Any]) -> WorkflowDefinition:
        """
        Build a WorkflowDefinition from a raw dict.
        """

        try:

            nodes = [
                self._load_node(node_data)
                for node_data in data.get("nodes", [])
            ]

            edges = [
                WorkflowEdge(**edge_data)
                for edge_data in data.get("edges", [])
            ]

            return WorkflowDefinition(
                name=data["name"],
                version=str(data["version"]),
                entry_node=data["entry_node"],
                nodes=nodes,
                edges=edges,
                description=data.get("description"),
                metadata=data.get("metadata", {}),
            )

        except KeyError as error:
            raise ValueError(
                f"Workflow definition is missing a required field: "
                f"{error}. Required fields: name, version, entry_node. "
                f"Each node requires: id, name, node_type."
            ) from error

    @staticmethod
    def _load_node(node_data: dict[str, Any]) -> WorkflowNode:

        retry_policy_data = node_data.get("retry_policy")

        return WorkflowNode(
            id=node_data["id"],
            name=node_data["name"],
            node_type=node_data["node_type"],
            configuration=node_data.get("configuration", {}),
            inputs=node_data.get("inputs", []),
            outputs=node_data.get("outputs", []),
            retry_policy=(
                RetryPolicy(**retry_policy_data)
                if retry_policy_data is not None
                else None
            ),
            timeout_seconds=node_data.get("timeout_seconds"),
            metadata=node_data.get("metadata", {}),
        )