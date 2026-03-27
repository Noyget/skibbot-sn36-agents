"""
Day 5: Form Navigation Agent for Bittensor Subnet 36

Core Responsibility:
  Extract form structure, detect navigation paths, validate fields, and track
  multi-step form state with high confidence and sub-10ms performance.

Architecture:
  - FormNavigationAgent: 10 navigation/interaction methods
  - FormFieldInfo, NavigationPath, FormState dataclasses for structured responses
  - 100% async/await with type hints
  - Loguru for observability
  - Error recovery for malformed/missing form data
  - JSON response with confidence scores (95%+ target)

Reference Pattern (Days 2-4):
  - Extract → Score → JSON response
  - Performance target: <10ms average
  - 100% type hints + dataclasses
  - Structured error handling
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional, Literal
from abc import ABC, abstractmethod
import json

from loguru import logger

# ─────────────────────────────────────────────────────────────────────────────
# Type System
# ─────────────────────────────────────────────────────────────────────────────


class FieldType(str, Enum):
    """Classification of HTML form field types."""
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    TEXTAREA = "textarea"
    FILE = "file"
    DATE = "date"
    TIME = "time"
    SUBMIT = "submit"
    BUTTON = "button"
    HIDDEN = "hidden"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    """Field validation outcome."""
    VALID = "valid"
    INVALID = "invalid"
    REQUIRED = "required"
    PATTERN_MISMATCH = "pattern_mismatch"
    LENGTH_VIOLATION = "length_violation"
    UNKNOWN = "unknown"


class NavigationType(str, Enum):
    """Form navigation action types."""
    CLICK_BUTTON = "click_button"
    FILL_FIELD = "fill_field"
    SELECT_OPTION = "select_option"
    NEXT_STEP = "next_step"
    PREV_STEP = "prev_step"
    SUBMIT = "submit"
    RESET = "reset"
    TAB_SWITCH = "tab_switch"
    MODAL_CLOSE = "modal_close"
    CONDITIONAL_BRANCH = "conditional_branch"


class FormFlowType(str, Enum):
    """Classification of multi-step form flows."""
    LINEAR = "linear"
    BRANCHING = "branching"
    CONDITIONAL = "conditional"
    WIZARD = "wizard"
    STEPPER = "stepper"
    TAB_BASED = "tab_based"
    MODAL = "modal"
    SINGLE_PAGE = "single_page"


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class FormFieldInfo:
    """Detailed metadata about a single form field."""
    name: str
    field_id: Optional[str]
    field_type: FieldType
    label: Optional[str]
    required: bool
    value: Optional[str]
    placeholder: Optional[str]
    validation_pattern: Optional[str]
    validation_status: ValidationStatus
    min_length: Optional[int]
    max_length: Optional[int]
    options: list[str] = field(default_factory=list)  # for select/radio/checkbox
    parent_step: Optional[int] = None
    visible: bool = True
    confidence: float = 0.85


@dataclass
class NavigationAction:
    """Single navigation action within a form."""
    action_type: NavigationType
    target_field: Optional[str]
    target_step: Optional[int]
    value: Optional[str]
    sequence_order: int
    requires_validation: bool = True
    confidence: float = 0.9


@dataclass
class NavigationPath:
    """Complete navigation sequence through a form."""
    path_id: str
    path_name: str
    start_step: int
    end_step: int
    actions: list[NavigationAction]
    flow_type: FormFlowType
    is_optimal: bool
    confidence: float
    estimated_interactions: int


@dataclass
class FormStep:
    """Single step/page in a multi-step form."""
    step_number: int
    step_title: Optional[str]
    fields: list[FormFieldInfo]
    is_current: bool
    is_completed: bool
    has_next: bool
    has_prev: bool
    navigation_buttons: list[str] = field(default_factory=list)


@dataclass
class FormState:
    """Complete state snapshot of a form at a point in time."""
    form_id: Optional[str]
    form_name: Optional[str]
    current_step: int
    total_steps: int
    flow_type: FormFlowType
    steps: list[FormStep]
    current_fields: list[FormFieldInfo]
    submission_ready: bool
    completion_percentage: float
    error_fields: list[str]
    validation_errors: list[str]
    form_data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.9


@dataclass
class FormNavigationResult:
    """Response structure for form navigation queries."""
    success: bool
    form_state: Optional[FormState]
    navigation_paths: list[NavigationPath]
    error_message: Optional[str]
    error_details: Optional[dict[str, Any]]
    confidence: float
    execution_time_ms: float
    recommendations: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON for API responses."""
        return json.dumps(asdict(self), default=str, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Form Navigation Agent
# ─────────────────────────────────────────────────────────────────────────────


class FormNavigationAgent:
    """
    Autonomous form navigation agent for Bittensor Subnet 36.
    
    Capabilities:
    - Form structure extraction and field detection
    - Field type classification and validation pattern recognition
    - Multi-step form flow analysis
    - Navigation path tracing and optimization
    - Form state persistence and recovery
    - Error detection and field-level validation
    - Submission readiness assessment
    
    Performance:
    - Target <10ms average execution time
    - 95%+ confidence scores on extractions
    - Async/await throughout for concurrency
    """

    def __init__(self, agent_id: str = "form_navigator_v1", debug: bool = False):
        """
        Initialize the Form Navigation Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            debug: Enable debug logging
        """
        self.agent_id = agent_id
        self.debug = debug
        self._form_cache: dict[str, FormState] = {}
        self._path_cache: dict[str, list[NavigationPath]] = {}
        
        logger.remove()  # Remove default handler
        logger.add(
            lambda msg: print(msg, end=""),
            format="<level>{level: <8}</level> | <level>{message}</level>",
            level="DEBUG" if debug else "INFO"
        )

    # ───────────────────────── Core Navigation Methods ───────────────────────

    async def extract_form_structure(
        self,
        html_content: str,
        form_selector: Optional[str] = None,
    ) -> FormNavigationResult:
        """
        Extract complete form structure from HTML.
        
        Args:
            html_content: Raw HTML content containing form
            form_selector: CSS selector for target form (optional)
            
        Returns:
            FormNavigationResult with extracted FormState
        """
        start_time = time.time()
        try:
            # Parse form element
            form_state = await self._parse_form_html(html_content, form_selector)
            
            if form_state is None:
                return FormNavigationResult(
                    success=False,
                    form_state=None,
                    navigation_paths=[],
                    error_message="No form found in provided HTML",
                    error_details={"selector": form_selector},
                    confidence=0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Cache the state
            if form_state.form_id:
                self._form_cache[form_state.form_id] = form_state
            
            logger.debug(f"Extracted form '{form_state.form_name}' with {len(form_state.current_fields)} fields")
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=[],
                error_message=None,
                error_details=None,
                confidence=form_state.confidence,
                execution_time_ms=(time.time() - start_time) * 1000,
                recommendations=self._generate_recommendations(form_state),
            )
            
        except Exception as e:
            logger.error(f"Form extraction failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=None,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def detect_navigation_paths(
        self,
        form_state: FormState,
        include_optimal_only: bool = False,
    ) -> FormNavigationResult:
        """
        Detect all possible navigation paths through the form.
        
        Args:
            form_state: Current form state
            include_optimal_only: Return only optimal paths
            
        Returns:
            FormNavigationResult with navigation paths
        """
        start_time = time.time()
        try:
            if form_state.form_id and form_state.form_id in self._path_cache:
                paths = self._path_cache[form_state.form_id]
            else:
                paths = await self._generate_navigation_paths(form_state)
                if form_state.form_id:
                    self._path_cache[form_state.form_id] = paths
            
            if include_optimal_only:
                paths = [p for p in paths if p.is_optimal]
            
            logger.debug(f"Detected {len(paths)} navigation path(s)")
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=paths,
                error_message=None,
                error_details=None,
                confidence=sum(p.confidence for p in paths) / len(paths) if paths else 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            logger.error(f"Path detection failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=form_state,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def validate_form_fields(
        self,
        form_state: FormState,
        field_data: dict[str, Any],
    ) -> FormNavigationResult:
        """
        Validate form fields against extracted patterns.
        
        Args:
            form_state: Current form state with field definitions
            field_data: Dictionary of field_name -> value pairs
            
        Returns:
            FormNavigationResult with validation status
        """
        start_time = time.time()
        try:
            updated_fields = await self._validate_fields(form_state.current_fields, field_data)
            
            # Update form state
            form_state.current_fields = updated_fields
            form_state.error_fields = [f.name for f in updated_fields if f.validation_status != ValidationStatus.VALID]
            form_state.submission_ready = len(form_state.error_fields) == 0 and not any(
                f.required and not f.value for f in updated_fields
            )
            
            logger.debug(f"Validation complete: {len(form_state.error_fields)} error(s)")
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=[],
                error_message=None,
                error_details=None,
                confidence=0.95,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            logger.error(f"Field validation failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=form_state,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def detect_multi_step_flow(
        self,
        form_state: FormState,
    ) -> FormNavigationResult:
        """
        Analyze and classify multi-step form flow.
        
        Args:
            form_state: Form state to analyze
            
        Returns:
            FormNavigationResult with flow analysis
        """
        start_time = time.time()
        try:
            flow_analysis = await self._analyze_flow_structure(form_state)
            form_state.flow_type = flow_analysis["flow_type"]
            
            logger.debug(f"Detected flow type: {flow_analysis['flow_type']}")
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=[],
                error_message=None,
                error_details=flow_analysis,
                confidence=flow_analysis.get("confidence", 0.9),
                execution_time_ms=(time.time() - start_time) * 1000,
                recommendations=flow_analysis.get("recommendations", []),
            )
            
        except Exception as e:
            logger.error(f"Flow detection failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=form_state,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def assess_submission_readiness(
        self,
        form_state: FormState,
    ) -> FormNavigationResult:
        """
        Assess whether form is ready for submission.
        
        Args:
            form_state: Form state to assess
            
        Returns:
            FormNavigationResult with submission readiness
        """
        start_time = time.time()
        try:
            readiness_data = await self._check_submission_readiness(form_state)
            form_state.submission_ready = readiness_data["is_ready"]
            form_state.completion_percentage = readiness_data["completion_percentage"]
            
            logger.debug(f"Submission readiness: {readiness_data['is_ready']} ({readiness_data['completion_percentage']:.1f}%)")
            
            recommendations = readiness_data.get("recommendations", [])
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=[],
                error_message=None,
                error_details=readiness_data,
                confidence=readiness_data.get("confidence", 0.95),
                execution_time_ms=(time.time() - start_time) * 1000,
                recommendations=recommendations,
            )
            
        except Exception as e:
            logger.error(f"Readiness assessment failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=form_state,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def trace_navigation_sequence(
        self,
        form_state: FormState,
        target_step: int,
    ) -> FormNavigationResult:
        """
        Trace optimal sequence of actions to reach target step.
        
        Args:
            form_state: Current form state
            target_step: Target step number
            
        Returns:
            FormNavigationResult with action sequence
        """
        start_time = time.time()
        try:
            if target_step < 0 or target_step >= form_state.total_steps:
                return FormNavigationResult(
                    success=False,
                    form_state=form_state,
                    navigation_paths=[],
                    error_message=f"Invalid target step {target_step}",
                    error_details={"valid_range": f"0-{form_state.total_steps - 1}"},
                    confidence=0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            sequence = await self._build_action_sequence(form_state, target_step)
            
            logger.debug(f"Traced sequence of {len(sequence.actions)} actions to step {target_step}")
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=[sequence],
                error_message=None,
                error_details=None,
                confidence=sequence.confidence,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            logger.error(f"Sequence tracing failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=form_state,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def detect_form_errors(
        self,
        form_state: FormState,
    ) -> FormNavigationResult:
        """
        Detect validation errors, missing required fields, and malformed form structure.
        
        Args:
            form_state: Form state to analyze
            
        Returns:
            FormNavigationResult with error analysis
        """
        start_time = time.time()
        try:
            errors = await self._analyze_form_errors(form_state)
            form_state.validation_errors = errors["validation_errors"]
            form_state.error_fields = errors["error_fields"]
            
            logger.debug(f"Detected {len(form_state.validation_errors)} error(s)")
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=[],
                error_message=None,
                error_details=errors,
                confidence=errors.get("confidence", 0.9),
                execution_time_ms=(time.time() - start_time) * 1000,
                recommendations=errors.get("recommendations", []),
            )
            
        except Exception as e:
            logger.error(f"Error detection failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=form_state,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def classify_field_types(
        self,
        html_content: str,
    ) -> FormNavigationResult:
        """
        Classify all form field types in HTML.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            FormNavigationResult with field classifications
        """
        start_time = time.time()
        try:
            field_classifications = await self._extract_field_types(html_content)
            
            logger.debug(f"Classified {len(field_classifications)} field(s)")
            
            return FormNavigationResult(
                success=True,
                form_state=None,
                navigation_paths=[],
                error_message=None,
                error_details={"field_types": field_classifications},
                confidence=0.92,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            logger.error(f"Field classification failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=None,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def persist_form_state(
        self,
        form_state: FormState,
        state_id: Optional[str] = None,
    ) -> FormNavigationResult:
        """
        Persist current form state for recovery/resume.
        
        Args:
            form_state: Form state to persist
            state_id: Optional custom state identifier
            
        Returns:
            FormNavigationResult with persistence confirmation
        """
        start_time = time.time()
        try:
            effective_id = state_id or form_state.form_id or f"form_state_{id(form_state)}"
            self._form_cache[effective_id] = form_state
            
            logger.debug(f"Persisted form state with id '{effective_id}'")
            
            return FormNavigationResult(
                success=True,
                form_state=form_state,
                navigation_paths=[],
                error_message=None,
                error_details={"persisted_id": effective_id},
                confidence=1.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            logger.error(f"State persistence failed: {e}")
            return FormNavigationResult(
                success=False,
                form_state=form_state,
                navigation_paths=[],
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    # ───────────────────────── Implementation Helpers ───────────────────────

    async def _parse_form_html(
        self,
        html_content: str,
        form_selector: Optional[str],
    ) -> Optional[FormState]:
        """Parse HTML to extract form structure."""
        # Simplified parsing (in production, use BeautifulSoup or lxml)
        import re
        
        form_id = None
        form_name = None
        fields = []
        
        # Extract form metadata from HTML patterns
        if '<form' in html_content or '<FORM' in html_content:
            form_match = re.search(r'<form[^>]*id=["\']?([^"\'>\s]+)["\']?', html_content, re.IGNORECASE)
            if form_match:
                form_id = form_match.group(1)
            
            name_match = re.search(r'<form[^>]*name=["\']?([^"\'>\s]+)["\']?', html_content, re.IGNORECASE)
            if name_match:
                form_name = name_match.group(1)
        
        # Extract input fields - improved pattern
        input_pattern = r'<input[^>]*>'
        
        for input_match in re.finditer(input_pattern, html_content, re.IGNORECASE):
            input_html = input_match.group(0)
            
            # Extract name
            name_match = re.search(r'name=["\']?([^"\'>\s]+)["\']?', input_html, re.IGNORECASE)
            name = name_match.group(1) if name_match else None
            
            if name:
                # Extract type (default to text)
                type_match = re.search(r'type=["\']?([^"\'>\s]+)["\']?', input_html, re.IGNORECASE)
                input_type = type_match.group(1).lower() if type_match else "text"
                
                try:
                    field_type = FieldType(input_type)
                except ValueError:
                    field_type = FieldType.UNKNOWN
                
                # Extract ID
                id_match = re.search(r'id=["\']?([^"\'>\s]+)["\']?', input_html, re.IGNORECASE)
                field_id = id_match.group(1) if id_match else None
                
                # Extract placeholder
                placeholder_match = re.search(r'placeholder=["\']?([^"\'>\s]+)["\']?', input_html, re.IGNORECASE)
                placeholder = placeholder_match.group(1) if placeholder_match else None
                
                # Check if required
                is_required = 'required' in input_html.lower()
                
                fields.append(FormFieldInfo(
                    name=name,
                    field_id=field_id,
                    field_type=field_type,
                    label=None,
                    required=is_required,
                    value=None,
                    placeholder=placeholder,
                    validation_pattern=None,
                    validation_status=ValidationStatus.UNKNOWN,
                    min_length=None,
                    max_length=None,
                    confidence=0.85,
                ))
        
        # Extract textareas
        textarea_pattern = r'<textarea[^>]*>'
        for textarea_match in re.finditer(textarea_pattern, html_content, re.IGNORECASE):
            textarea_html = textarea_match.group(0)
            name_match = re.search(r'name=["\']?([^"\'>\s]+)["\']?', textarea_html, re.IGNORECASE)
            name = name_match.group(1) if name_match else None
            
            if name:
                fields.append(FormFieldInfo(
                    name=name,
                    field_id=None,
                    field_type=FieldType.TEXTAREA,
                    label=None,
                    required='required' in textarea_html.lower(),
                    value=None,
                    placeholder=None,
                    validation_pattern=None,
                    validation_status=ValidationStatus.UNKNOWN,
                    min_length=None,
                    max_length=None,
                    confidence=0.85,
                ))
        
        # Extract selects
        select_pattern = r'<select[^>]*>'
        for select_match in re.finditer(select_pattern, html_content, re.IGNORECASE):
            select_html = select_match.group(0)
            name_match = re.search(r'name=["\']?([^"\'>\s]+)["\']?', select_html, re.IGNORECASE)
            name = name_match.group(1) if name_match else None
            
            if name:
                fields.append(FormFieldInfo(
                    name=name,
                    field_id=None,
                    field_type=FieldType.SELECT,
                    label=None,
                    required='required' in select_html.lower(),
                    value=None,
                    placeholder=None,
                    validation_pattern=None,
                    validation_status=ValidationStatus.UNKNOWN,
                    min_length=None,
                    max_length=None,
                    confidence=0.85,
                ))
        
        if not fields:
            return None
        
        return FormState(
            form_id=form_id,
            form_name=form_name,
            current_step=0,
            total_steps=1,
            flow_type=FormFlowType.SINGLE_PAGE,
            steps=[FormStep(
                step_number=0,
                step_title="Form",
                fields=fields,
                is_current=True,
                is_completed=False,
                has_next=False,
                has_prev=False,
            )],
            current_fields=fields,
            submission_ready=False,
            completion_percentage=0.0,
            error_fields=[],
            validation_errors=[],
            confidence=0.88,
        )

    async def _validate_fields(
        self,
        fields: list[FormFieldInfo],
        field_data: dict[str, Any],
    ) -> list[FormFieldInfo]:
        """Validate fields against provided data."""
        validated = []
        for field in fields:
            value = field_data.get(field.name)
            status = ValidationStatus.UNKNOWN
            
            if field.required and not value:
                status = ValidationStatus.REQUIRED
            elif value:
                if field.field_type == FieldType.EMAIL:
                    import re
                    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(value)):
                        status = ValidationStatus.VALID
                    else:
                        status = ValidationStatus.PATTERN_MISMATCH
                elif field.field_type == FieldType.NUMBER:
                    try:
                        float(value)
                        status = ValidationStatus.VALID
                    except ValueError:
                        status = ValidationStatus.PATTERN_MISMATCH
                elif field.min_length and len(str(value)) < field.min_length:
                    status = ValidationStatus.LENGTH_VIOLATION
                elif field.max_length and len(str(value)) > field.max_length:
                    status = ValidationStatus.LENGTH_VIOLATION
                else:
                    status = ValidationStatus.VALID
            
            field.validation_status = status
            field.value = value
            validated.append(field)
        
        return validated

    async def _generate_navigation_paths(
        self,
        form_state: FormState,
    ) -> list[NavigationPath]:
        """Generate possible navigation paths through form."""
        if form_state.total_steps <= 1:
            # Single page form has one path
            actions = [
                NavigationAction(
                    action_type=NavigationType.FILL_FIELD,
                    target_field=f.name,
                    target_step=0,
                    value=None,
                    sequence_order=i,
                    confidence=0.9,
                )
                for i, f in enumerate(form_state.current_fields)
            ]
            actions.append(NavigationAction(
                action_type=NavigationType.SUBMIT,
                target_field=None,
                target_step=None,
                value=None,
                sequence_order=len(actions),
                confidence=0.95,
            ))
            
            return [NavigationPath(
                path_id="single_page_0",
                path_name="Standard Flow",
                start_step=0,
                end_step=0,
                actions=actions,
                flow_type=FormFlowType.SINGLE_PAGE,
                is_optimal=True,
                confidence=0.92,
                estimated_interactions=len(actions),
            )]
        else:
            # Multi-step form
            paths = []
            for i in range(form_state.total_steps - 1):
                actions = [
                    NavigationAction(
                        action_type=NavigationType.NEXT_STEP,
                        target_field=None,
                        target_step=i + 1,
                        value=None,
                        sequence_order=j,
                        confidence=0.95,
                    )
                    for j in range(i + 1)
                ]
                
                paths.append(NavigationPath(
                    path_id=f"linear_{i}",
                    path_name=f"Forward to Step {i + 1}",
                    start_step=i,
                    end_step=i + 1,
                    actions=actions,
                    flow_type=FormFlowType.LINEAR,
                    is_optimal=i == 0,
                    confidence=0.93,
                    estimated_interactions=len(actions),
                ))
            
            return paths

    async def _analyze_flow_structure(
        self,
        form_state: FormState,
    ) -> dict[str, Any]:
        """Analyze form flow structure."""
        flow_type = FormFlowType.SINGLE_PAGE
        
        if form_state.total_steps > 1:
            # Heuristic: check for next/prev buttons
            flow_type = FormFlowType.LINEAR  # Simple assumption
        
        return {
            "flow_type": flow_type,
            "total_steps": form_state.total_steps,
            "current_step": form_state.current_step,
            "confidence": 0.90,
            "recommendations": [
                "Fill all required fields before proceeding",
                "Use Next button to advance through steps",
            ] if form_state.total_steps > 1 else [],
        }

    async def _check_submission_readiness(
        self,
        form_state: FormState,
    ) -> dict[str, Any]:
        """Check if form is ready for submission."""
        required_fields = [f for f in form_state.current_fields if f.required]
        filled_required = [f for f in required_fields if f.value]
        completion = len(filled_required) / len(required_fields) if required_fields else 1.0
        
        is_ready = (
            completion == 1.0 and
            all(f.validation_status == ValidationStatus.VALID for f in form_state.current_fields if f.value)
        )
        
        recommendations = []
        if not is_ready:
            missing = [f.name for f in required_fields if not f.value]
            if missing:
                recommendations.append(f"Fill required fields: {', '.join(missing)}")
        
        return {
            "is_ready": is_ready,
            "completion_percentage": completion * 100,
            "confidence": 0.95,
            "recommendations": recommendations,
        }

    async def _build_action_sequence(
        self,
        form_state: FormState,
        target_step: int,
    ) -> NavigationPath:
        """Build action sequence to reach target step."""
        actions = []
        
        if target_step > form_state.current_step:
            for i in range(target_step - form_state.current_step):
                actions.append(NavigationAction(
                    action_type=NavigationType.NEXT_STEP,
                    target_field=None,
                    target_step=form_state.current_step + i + 1,
                    value=None,
                    sequence_order=i,
                    confidence=0.95,
                ))
        elif target_step < form_state.current_step:
            for i in range(form_state.current_step - target_step):
                actions.append(NavigationAction(
                    action_type=NavigationType.PREV_STEP,
                    target_field=None,
                    target_step=form_state.current_step - i - 1,
                    value=None,
                    sequence_order=i,
                    confidence=0.95,
                ))
        
        return NavigationPath(
            path_id=f"sequence_{form_state.current_step}_to_{target_step}",
            path_name=f"Navigate to Step {target_step}",
            start_step=form_state.current_step,
            end_step=target_step,
            actions=actions,
            flow_type=form_state.flow_type,
            is_optimal=True,
            confidence=0.94,
            estimated_interactions=len(actions),
        )

    async def _analyze_form_errors(
        self,
        form_state: FormState,
    ) -> dict[str, Any]:
        """Analyze form for errors."""
        validation_errors = []
        error_fields = []
        
        for field in form_state.current_fields:
            if field.validation_status != ValidationStatus.VALID and field.validation_status != ValidationStatus.UNKNOWN:
                error_fields.append(field.name)
                validation_errors.append({
                    "field": field.name,
                    "status": field.validation_status.value,
                    "message": f"Validation failed: {field.validation_status.value}",
                })
            elif field.required and not field.value:
                error_fields.append(field.name)
                validation_errors.append({
                    "field": field.name,
                    "status": "required",
                    "message": "This field is required",
                })
        
        recommendations = [
            f"Fix validation error in field '{f}'" for f in error_fields
        ]
        
        return {
            "validation_errors": validation_errors,
            "error_fields": error_fields,
            "error_count": len(error_fields),
            "confidence": 0.92,
            "recommendations": recommendations,
        }

    async def _extract_field_types(
        self,
        html_content: str,
    ) -> list[dict[str, Any]]:
        """Extract and classify field types from HTML."""
        import re
        
        field_classifications = []
        
        # Input fields - improved pattern
        input_pattern = r'<input[^>]*>'
        for input_match in re.finditer(input_pattern, html_content, re.IGNORECASE):
            input_html = input_match.group(0)
            
            # Extract name
            name_match = re.search(r'name=["\']?([^"\'>\s]+)["\']?', input_html, re.IGNORECASE)
            name = name_match.group(1) if name_match else None
            
            if name:
                # Extract type
                type_match = re.search(r'type=["\']?([^"\'>\s]+)["\']?', input_html, re.IGNORECASE)
                input_type = type_match.group(1).lower() if type_match else "text"
                
                try:
                    field_type = FieldType(input_type)
                except ValueError:
                    field_type = FieldType.UNKNOWN
                
                field_classifications.append({
                    "name": name,
                    "type": field_type.value,
                    "html_element": "input",
                })
        
        # Textareas - improved pattern
        textarea_pattern = r'<textarea[^>]*>'
        for textarea_match in re.finditer(textarea_pattern, html_content, re.IGNORECASE):
            textarea_html = textarea_match.group(0)
            name_match = re.search(r'name=["\']?([^"\'>\s]+)["\']?', textarea_html, re.IGNORECASE)
            name = name_match.group(1) if name_match else None
            
            if name:
                field_classifications.append({
                    "name": name,
                    "type": FieldType.TEXTAREA.value,
                    "html_element": "textarea",
                })
        
        # Select elements - improved pattern
        select_pattern = r'<select[^>]*>'
        for select_match in re.finditer(select_pattern, html_content, re.IGNORECASE):
            select_html = select_match.group(0)
            name_match = re.search(r'name=["\']?([^"\'>\s]+)["\']?', select_html, re.IGNORECASE)
            name = name_match.group(1) if name_match else None
            
            if name:
                field_classifications.append({
                    "name": name,
                    "type": FieldType.SELECT.value,
                    "html_element": "select",
                })
        
        return field_classifications

    def _generate_recommendations(self, form_state: FormState) -> list[str]:
        """Generate user-friendly recommendations."""
        recommendations = []
        
        if form_state.total_steps > 1:
            recommendations.append(f"This is a {form_state.total_steps}-step form. Start by filling required fields on step 1.")
        
        required = [f for f in form_state.current_fields if f.required]
        if required:
            recommendations.append(f"Required fields: {', '.join(f.name for f in required)}")
        
        return recommendations

    async def solve_form_task(
        self,
        html: str,
        prompt: str,
        max_steps: int = 12,
    ) -> list[dict[str, Any]]:
        """
        Solve form-based task by generating action sequence.
        
        This is the critical new method that converts form analysis into
        executable browser actions for validators.
        
        Args:
            html: Form HTML content
            prompt: Task description (e.g., "Fill email with user@example.com and submit")
            max_steps: Maximum number of actions to generate (default 12)
            
        Returns:
            List of actions that validators can execute:
            [
                {"type": "click", "selector": "[name='email']"},
                {"type": "input", "selector": "[name='email']", "value": "user@example.com"},
                {"type": "click", "selector": "button[type='submit']"}
            ]
        """
        import re
        
        actions = []
        start_time = time.time()
        
        try:
            # Step 1: Analyze form structure using existing extract_form_structure
            analysis = await self.extract_form_structure(html_content=html)
            if not analysis.success or not analysis.form_state:
                logger.warning(f"Form analysis failed: {analysis.error_message}")
                return []
            
            # Step 2: Extract task requirements from prompt using regex patterns
            prompt_lower = prompt.lower()
            field_values = {}
            
            # Email pattern
            email_match = re.search(
                r'(?:email|e-mail)[:\s]+([^\s,\.;\n]+@[^\s,\.;\n]+)',
                prompt_lower
            )
            if email_match:
                field_values['email'] = email_match.group(1)
            
            # Name pattern
            name_match = re.search(
                r'(?:name|full name)[:\s]+([^,\.;\n]+?)(?=\s+and|\s*$)',
                prompt_lower
            )
            if name_match:
                field_values['name'] = name_match.group(1).strip()
            
            # Password pattern
            pwd_match = re.search(
                r'(?:password|pass)[:\s]+([^\s,\.;\n]+)',
                prompt_lower
            )
            if pwd_match:
                field_values['password'] = pwd_match.group(1)
            
            # Generic key=value pattern
            kv_matches = re.finditer(
                r'(\w+)[:\s]+([^\s,\.;]+)',
                prompt_lower
            )
            for match in kv_matches:
                key, value = match.groups()
                if key not in field_values:
                    field_values[key] = value
            
            # Step 3: Generate click + input actions for each identified field
            for field in analysis.form_state.current_fields:
                field_name_lower = field.name.lower()
                
                # Find value for this field by matching prompt keywords
                field_value = None
                for key, value in field_values.items():
                    if key in field_name_lower or field_name_lower in key:
                        field_value = value
                        break
                
                # If we have a value for this field, click + input
                if field_value and field.field_type != FieldType.SUBMIT:
                    # FIX #3: Add wait_for_element action before clicking
                    # This ensures async page content has loaded
                    actions.append({
                        "type": "wait_for_element",
                        "selector": f"[name='{field.name}']",
                        "timeout": 5000,
                        "visible": True,
                        "clickable": True,
                        "reason": f"Wait for field '{field.name}' to load and be interactive"
                    })
                    
                    # FIX #2: Click action with retry logic and alternative selectors
                    actions.append({
                        "type": "click",
                        "selector": f"[name='{field.name}']",
                        "alternative_selectors": [
                            f"#{field.name}",  # Try ID if name fails
                            f"input[name='{field.name}']",  # Explicit tag
                            f"[data-field='{field.name}']",  # Data attribute
                            f"input#{field.name}",  # Combo: tag + ID
                        ],
                        "retry_count": 3,
                        "retry_delay": 500,
                        "reason": f"Focus field '{field.name}' for input (with fallback selectors)"
                    })
                    
                    # Input action to fill field
                    # ✅ FIX #2: Use "text" not "value" (validators expect TypeAction.text)
                    actions.append({
                        "type": "input",
                        "selector": f"[name='{field.name}']",
                        "alternative_selectors": [
                            f"#{field.name}",
                            f"input[name='{field.name}']",
                            f"[data-field='{field.name}']",
                        ],
                        "text": field_value,  # ✅ CHANGED from "value" to "text"
                        "retry_count": 3,
                        "reason": f"Fill {field.field_type.value} field '{field.name}' (with fallback selectors)"
                    })
            
            # Step 4: Find and click submit button
            # Priority: look for explicit submit in form fields
            submit_found = False
            for field in analysis.form_state.current_fields:
                if field.field_type == FieldType.SUBMIT:
                    # FIX #3: Wait for submit button to be interactive
                    actions.append({
                        "type": "wait_for_element",
                        "selector": f"[name='{field.name}']",
                        "timeout": 5000,
                        "clickable": True,
                        "reason": "Wait for submit button to be clickable"
                    })
                    
                    # FIX #2 & #6: Click with retry and multiple selector strategies
                    actions.append({
                        "type": "click",
                        "selector": f"[name='{field.name}']",
                        "alternative_selectors": [
                            f"#{field.name}",
                            f"input[type='submit']",
                            f"[type='submit']",
                        ],
                        "retry_count": 3,
                        "reason": "Click submit button (with fallback selectors)"
                    })
                    submit_found = True
                    break
            
            # If no submit field found, look for submit button or similar
            if not submit_found:
                # FIX #3: Wait for submit button before clicking
                actions.append({
                    "type": "wait_for_element",
                    "selector": "button[type='submit']",
                    "timeout": 5000,
                    "clickable": True,
                    "reason": "Wait for submit button to appear and be clickable"
                })
                
                # FIX #6: Use valid CSS selectors only (no jQuery :contains)
                # Try multiple strategies in order
                submit_selectors = [
                    "button[type='submit']",        # Standard submit button
                    "input[type='submit']",         # Submit input
                    "[type='submit']",              # Any submit element
                    "button.submit",                # Class-based
                    "button.btn-primary",           # Bootstrap primary
                    "button.btn-success",           # Bootstrap success
                    "button.btn:not([type='button'])",  # Any button except explicit button type
                ]
                
                # FIX #2: Pass list of selectors with retry logic
                # Validator will try each until one works
                actions.append({
                    "type": "click",
                    "selector": submit_selectors,  # Pass list of alternatives
                    "retry_count": 3,
                    "timeout": 5000,
                    "reason": "Click form submit button (tries multiple selector strategies)"
                })
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(
                f"solve_form_task generated {len(actions)} actions in {execution_time:.2f}ms"
            )
            
            # Respect max_steps limit
            return actions[:max_steps]
        
        except Exception as e:
            logger.error(f"Error in solve_form_task: {e}", exc_info=True)
            return []


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Integration
# ─────────────────────────────────────────────────────────────────────────────


async def handle_form_navigation_request(
    action: Literal[
        "extract_form",
        "detect_paths",
        "validate_fields",
        "detect_flow",
        "assess_readiness",
        "trace_sequence",
        "detect_errors",
        "classify_fields",
    ],
    payload: dict[str, Any],
    agent: Optional[FormNavigationAgent] = None,
) -> FormNavigationResult:
    """
    HTTP /act endpoint handler for form navigation requests.
    
    Args:
        action: Type of navigation action
        payload: Request payload
        agent: FormNavigationAgent instance (uses default if None)
        
    Returns:
        FormNavigationResult (auto-serializable to JSON)
    """
    if agent is None:
        agent = FormNavigationAgent()
    
    try:
        if action == "extract_form":
            return await agent.extract_form_structure(
                html_content=payload.get("html", ""),
                form_selector=payload.get("selector"),
            )
        
        elif action == "detect_paths":
            form_state = payload.get("form_state")
            if not form_state:
                return FormNavigationResult(
                    success=False,
                    form_state=None,
                    navigation_paths=[],
                    error_message="form_state required",
                    error_details=None,
                    confidence=0.0,
                    execution_time_ms=0.0,
                )
            # Reconstruct FormState from dict
            form_state = _reconstruct_form_state(form_state)
            return await agent.detect_navigation_paths(
                form_state=form_state,
                include_optimal_only=payload.get("optimal_only", False),
            )
        
        elif action == "validate_fields":
            form_state = _reconstruct_form_state(payload.get("form_state", {}))
            return await agent.validate_form_fields(
                form_state=form_state,
                field_data=payload.get("field_data", {}),
            )
        
        elif action == "detect_flow":
            form_state = _reconstruct_form_state(payload.get("form_state", {}))
            return await agent.detect_multi_step_flow(form_state=form_state)
        
        elif action == "assess_readiness":
            form_state = _reconstruct_form_state(payload.get("form_state", {}))
            return await agent.assess_submission_readiness(form_state=form_state)
        
        elif action == "trace_sequence":
            form_state = _reconstruct_form_state(payload.get("form_state", {}))
            return await agent.trace_navigation_sequence(
                form_state=form_state,
                target_step=payload.get("target_step", 0),
            )
        
        elif action == "detect_errors":
            form_state = _reconstruct_form_state(payload.get("form_state", {}))
            return await agent.detect_form_errors(form_state=form_state)
        
        elif action == "classify_fields":
            return await agent.classify_field_types(
                html_content=payload.get("html", ""),
            )
        
        else:
            return FormNavigationResult(
                success=False,
                form_state=None,
                navigation_paths=[],
                error_message=f"Unknown action: {action}",
                error_details=None,
                confidence=0.0,
                execution_time_ms=0.0,
            )
    
    except Exception as e:
        logger.error(f"Request handler error: {e}")
        return FormNavigationResult(
            success=False,
            form_state=None,
            navigation_paths=[],
            error_message=str(e),
            error_details={"exception_type": type(e).__name__},
            confidence=0.0,
            execution_time_ms=0.0,
        )


def _reconstruct_form_state(data: dict[str, Any]) -> FormState:
    """Reconstruct FormState from dictionary."""
    if not data:
        return FormState(
            form_id=None,
            form_name=None,
            current_step=0,
            total_steps=1,
            flow_type=FormFlowType.SINGLE_PAGE,
            steps=[],
            current_fields=[],
            submission_ready=False,
            completion_percentage=0.0,
            error_fields=[],
            validation_errors=[],
        )
    
    return FormState(
        form_id=data.get("form_id"),
        form_name=data.get("form_name"),
        current_step=data.get("current_step", 0),
        total_steps=data.get("total_steps", 1),
        flow_type=FormFlowType(data.get("flow_type", FormFlowType.SINGLE_PAGE.value)),
        steps=data.get("steps", []),
        current_fields=data.get("current_fields", []),
        submission_ready=data.get("submission_ready", False),
        completion_percentage=data.get("completion_percentage", 0.0),
        error_fields=data.get("error_fields", []),
        validation_errors=data.get("validation_errors", []),
        form_data=data.get("form_data", {}),
    )
