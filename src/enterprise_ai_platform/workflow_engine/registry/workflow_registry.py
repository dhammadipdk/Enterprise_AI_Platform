"""
Workflow registry.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.workflow_engine.graph import WorkflowGraph


class WorkflowRegistry(BaseRegistry[WorkflowGraph]):
    """
    Registry of compiled workflow graphs, keyed by "name@version".
    """

    pass