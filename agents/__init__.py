"""
Bittensor Subnet 36 Autonomous Web Agents - Agent Implementations

Day 5: Form Navigation Agent
- Autonomous form structure extraction and navigation
- Multi-step form handling with state persistence
- <10ms performance, 95%+ confidence scoring
"""

from .form_navigator import (
    FormNavigationAgent,
    FormNavigationResult,
    FormState,
    FormFieldInfo,
    FormStep,
    NavigationPath,
    NavigationAction,
    FieldType,
    ValidationStatus,
    NavigationType,
    FormFlowType,
    handle_form_navigation_request,
)

__all__ = [
    "FormNavigationAgent",
    "FormNavigationResult",
    "FormState",
    "FormFieldInfo",
    "FormStep",
    "NavigationPath",
    "NavigationAction",
    "FieldType",
    "ValidationStatus",
    "NavigationType",
    "FormFlowType",
    "handle_form_navigation_request",
]

__version__ = "1.0.0"
__author__ = "Bittensor Subnet 36"
