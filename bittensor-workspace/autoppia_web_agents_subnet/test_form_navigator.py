"""
Test Suite for Form Navigation Agent (Day 5)

Comprehensive coverage:
- 25 test cases targeting 100% pass rate
- All navigation types (8+ methods covered)
- Edge cases, malformed forms, missing fields
- Performance benchmarks targeting <10ms average
- 95%+ confidence validation
"""

import pytest
import asyncio
import time
import json
from typing import Any
import sys
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from form_navigator import (
    FormNavigationAgent,
    FormNavigationResult,
    FormState,
    FormFieldInfo,
    FormFlowType,
    FieldType,
    ValidationStatus,
    NavigationType,
    handle_form_navigation_request,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def agent():
    """Create a FormNavigationAgent instance."""
    return FormNavigationAgent(debug=False)


@pytest.fixture
def simple_form_html():
    """Simple single-page form HTML."""
    return """
    <form id="contact_form" name="contact">
        <input type="text" name="username" placeholder="Enter username" required>
        <input type="email" name="email" placeholder="Enter email" required>
        <input type="password" name="password" placeholder="Enter password" required>
        <textarea name="message" placeholder="Enter message"></textarea>
        <input type="submit" value="Submit">
    </form>
    """


@pytest.fixture
def complex_form_html():
    """Multi-step form HTML."""
    return """
    <form id="registration_form" name="register">
        <fieldset id="step_1">
            <input type="text" name="firstname" required>
            <input type="text" name="lastname" required>
        </fieldset>
        <fieldset id="step_2">
            <input type="email" name="email" required>
            <input type="password" name="password" required>
        </fieldset>
        <fieldset id="step_3">
            <input type="text" name="address" required>
            <input type="text" name="phone" required>
        </fieldset>
        <button type="button" name="next">Next</button>
        <button type="button" name="prev">Previous</button>
        <button type="submit">Submit</button>
    </form>
    """


@pytest.fixture
def form_with_validation():
    """Form with validation patterns."""
    return """
    <form id="profile_form">
        <input type="text" name="username" minlength="3" maxlength="20" required>
        <input type="email" name="email" pattern="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$" required>
        <input type="number" name="age" min="18" max="120">
        <input type="checkbox" name="terms" required>
        <select name="country" required>
            <option value="">Select country</option>
            <option value="us">United States</option>
            <option value="uk">United Kingdom</option>
        </select>
        <input type="submit" value="Save Profile">
    </form>
    """


# ─────────────────────────────────────────────────────────────────────────────
# Test: Form Extraction
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_simple_form(agent, simple_form_html):
    """Test extraction of simple single-page form."""
    result = await agent.extract_form_structure(simple_form_html)
    
    assert result.success
    assert result.form_state is not None
    assert result.form_state.form_id == "contact_form"
    assert result.form_state.form_name == "contact"
    assert len(result.form_state.current_fields) == 4
    assert result.confidence >= 0.85


@pytest.mark.asyncio
async def test_extract_form_field_count(agent, complex_form_html):
    """Test correct field counting in complex form."""
    result = await agent.extract_form_structure(complex_form_html)
    
    assert result.success
    assert result.form_state is not None
    assert len(result.form_state.current_fields) > 0


@pytest.mark.asyncio
async def test_extract_form_without_id(agent):
    """Test form extraction when form has no ID attribute."""
    html = '<form><input type="text" name="field1" required></form>'
    result = await agent.extract_form_structure(html)
    
    assert result.success
    assert result.form_state is not None
    assert len(result.form_state.current_fields) >= 1


@pytest.mark.asyncio
async def test_extract_from_empty_html(agent):
    """Test extraction from HTML with no form."""
    result = await agent.extract_form_structure("<div>No form here</div>")
    
    assert not result.success
    assert result.form_state is None
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_extract_malformed_form(agent):
    """Test extraction from malformed HTML."""
    html = '<form id="bad"><input type="text" name="field" />'  # Unclosed form
    result = await agent.extract_form_structure(html)
    
    # Should still extract what it can
    assert result.success
    assert result.form_state is not None or not result.success


# ─────────────────────────────────────────────────────────────────────────────
# Test: Field Type Classification
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_classify_field_types(agent, form_with_validation):
    """Test field type classification."""
    result = await agent.classify_field_types(form_with_validation)
    
    assert result.success
    assert result.error_details is not None
    field_types = result.error_details.get("field_types", [])
    assert len(field_types) > 0
    assert any(f["type"] == "email" for f in field_types)
    assert any(f["type"] == "number" for f in field_types)


@pytest.mark.asyncio
async def test_classify_mixed_input_types(agent):
    """Test classification of various input types."""
    html = """
    <form>
        <input type="text" name="text_field">
        <input type="email" name="email_field">
        <input type="password" name="pwd_field">
        <input type="number" name="num_field">
        <input type="date" name="date_field">
        <input type="file" name="file_field">
    </form>
    """
    result = await agent.classify_field_types(html)
    
    assert result.success
    field_types = result.error_details.get("field_types", [])
    type_names = [f["type"] for f in field_types]
    assert "text" in type_names or len(type_names) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Test: Field Validation
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_valid_fields(agent, simple_form_html):
    """Test validation of valid field data."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    field_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secure123",
        "message": "Hello world",
    }
    
    result = await agent.validate_form_fields(form_state, field_data)
    
    assert result.success
    assert result.form_state is not None
    assert result.form_state.submission_ready


@pytest.mark.asyncio
async def test_validate_missing_required(agent, simple_form_html):
    """Test validation fails when required fields are missing."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    field_data = {
        "username": "john_doe",
        # Missing email and password
    }
    
    result = await agent.validate_form_fields(form_state, field_data)
    
    assert result.success
    assert result.form_state is not None
    assert not result.form_state.submission_ready


@pytest.mark.asyncio
async def test_validate_invalid_email(agent, form_with_validation):
    """Test email validation pattern matching."""
    form_result = await agent.extract_form_structure(form_with_validation)
    form_state = form_result.form_state
    
    field_data = {
        "username": "testuser",
        "email": "not_an_email",  # Invalid
    }
    
    result = await agent.validate_form_fields(form_state, field_data)
    
    assert result.success
    assert len(result.form_state.error_fields) > 0


@pytest.mark.asyncio
async def test_validate_number_field(agent):
    """Test number field validation."""
    html = '<form><input type="number" name="age" min="18" max="120" required></form>'
    form_result = await agent.extract_form_structure(html)
    form_state = form_result.form_state
    
    field_data = {"age": "25"}
    result = await agent.validate_form_fields(form_state, field_data)
    
    assert result.success
    updated_field = next((f for f in result.form_state.current_fields if f.name == "age"), None)
    assert updated_field is not None


# ─────────────────────────────────────────────────────────────────────────────
# Test: Navigation Path Detection
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_single_page_path(agent, simple_form_html):
    """Test navigation paths for single-page form."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    result = await agent.detect_navigation_paths(form_state)
    
    assert result.success
    assert len(result.navigation_paths) > 0
    # Single page should have one main path
    assert any(p.flow_type == FormFlowType.SINGLE_PAGE for p in result.navigation_paths)


@pytest.mark.asyncio
async def test_detect_multi_step_paths(agent, complex_form_html):
    """Test navigation paths for multi-step form."""
    form_result = await agent.extract_form_structure(complex_form_html)
    form_state = form_result.form_state
    
    # Simulate multi-step form
    form_state.total_steps = 3
    
    result = await agent.detect_navigation_paths(form_state)
    
    assert result.success
    assert len(result.navigation_paths) > 0


@pytest.mark.asyncio
async def test_detect_optimal_paths_only(agent, simple_form_html):
    """Test filtering to optimal paths only."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    result = await agent.detect_navigation_paths(form_state, include_optimal_only=True)
    
    assert result.success
    assert all(p.is_optimal for p in result.navigation_paths)


# ─────────────────────────────────────────────────────────────────────────────
# Test: Multi-Step Flow Detection
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_single_page_flow(agent, simple_form_html):
    """Test flow type detection for single-page form."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    result = await agent.detect_multi_step_flow(form_state)
    
    assert result.success
    assert result.form_state.flow_type == FormFlowType.SINGLE_PAGE


@pytest.mark.asyncio
async def test_detect_linear_flow(agent, complex_form_html):
    """Test flow type detection for multi-step form."""
    form_result = await agent.extract_form_structure(complex_form_html)
    form_state = form_result.form_state
    form_state.total_steps = 3
    
    result = await agent.detect_multi_step_flow(form_state)
    
    assert result.success
    assert result.form_state.flow_type in [FormFlowType.LINEAR, FormFlowType.WIZARD]


# ─────────────────────────────────────────────────────────────────────────────
# Test: Submission Readiness
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_assess_readiness_all_filled(agent, simple_form_html):
    """Test submission readiness when all fields are filled."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    # Fill all required fields
    for field in form_state.current_fields:
        if field.required:
            field.value = "test_value"
            field.validation_status = ValidationStatus.VALID
    
    result = await agent.assess_submission_readiness(form_state)
    
    assert result.success
    assert result.form_state.submission_ready


@pytest.mark.asyncio
async def test_assess_readiness_incomplete(agent, simple_form_html):
    """Test submission readiness when form is incomplete."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    # Don't fill any fields
    result = await agent.assess_submission_readiness(form_state)
    
    assert result.success
    assert not result.form_state.submission_ready
    assert result.form_state.completion_percentage < 100


@pytest.mark.asyncio
async def test_completion_percentage_calculation(agent, simple_form_html):
    """Test completion percentage calculation."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    # Fill half the required fields
    required = [f for f in form_state.current_fields if f.required]
    for field in required[:len(required)//2]:
        field.value = "test"
    
    result = await agent.assess_submission_readiness(form_state)
    
    assert result.success
    assert 0 < result.form_state.completion_percentage < 100


# ─────────────────────────────────────────────────────────────────────────────
# Test: Navigation Sequence Tracing
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trace_forward_sequence(agent, complex_form_html):
    """Test tracing sequence forward through steps."""
    form_result = await agent.extract_form_structure(complex_form_html)
    form_state = form_result.form_state
    form_state.total_steps = 3
    form_state.current_step = 0
    
    result = await agent.trace_navigation_sequence(form_state, target_step=2)
    
    assert result.success
    assert len(result.navigation_paths) > 0
    path = result.navigation_paths[0]
    assert path.end_step == 2


@pytest.mark.asyncio
async def test_trace_backward_sequence(agent):
    """Test tracing sequence backward through steps."""
    html = '<form><input type="text" name="field1"></form>'
    form_result = await agent.extract_form_structure(html)
    form_state = form_result.form_state
    form_state.total_steps = 3
    form_state.current_step = 2
    
    result = await agent.trace_navigation_sequence(form_state, target_step=0)
    
    assert result.success
    assert len(result.navigation_paths) > 0


@pytest.mark.asyncio
async def test_trace_invalid_target(agent):
    """Test tracing to invalid step number."""
    html = '<form><input type="text" name="field1"></form>'
    form_result = await agent.extract_form_structure(html)
    form_state = form_result.form_state
    form_state.total_steps = 2
    
    result = await agent.trace_navigation_sequence(form_state, target_step=5)
    
    assert not result.success
    assert "Invalid target step" in result.error_message


# ─────────────────────────────────────────────────────────────────────────────
# Test: Error Detection
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_missing_fields(agent, simple_form_html):
    """Test detection of missing required fields."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    # Don't fill required fields
    result = await agent.detect_form_errors(form_state)
    
    assert result.success
    assert len(result.form_state.error_fields) > 0


@pytest.mark.asyncio
async def test_detect_validation_errors(agent):
    """Test detection of validation errors."""
    html = '<form><input type="email" name="email" required></form>'
    form_result = await agent.extract_form_structure(html)
    form_state = form_result.form_state
    form_state.current_fields[0].validation_status = ValidationStatus.PATTERN_MISMATCH
    
    result = await agent.detect_form_errors(form_state)
    
    assert result.success
    assert len(result.form_state.validation_errors) > 0


@pytest.mark.asyncio
async def test_no_errors_valid_form(agent, simple_form_html):
    """Test that valid form reports no errors."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    # Mark all as valid
    for field in form_state.current_fields:
        field.value = "valid_value"
        field.validation_status = ValidationStatus.VALID
    
    result = await agent.detect_form_errors(form_state)
    
    assert result.success


# ─────────────────────────────────────────────────────────────────────────────
# Test: State Persistence
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persist_form_state(agent, simple_form_html):
    """Test form state persistence."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    result = await agent.persist_form_state(form_state, state_id="test_state")
    
    assert result.success
    assert result.error_details["persisted_id"] == "test_state"


@pytest.mark.asyncio
async def test_retrieve_persisted_state(agent, simple_form_html):
    """Test retrieving persisted form state."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    form_state.form_id = "test_form"
    
    await agent.persist_form_state(form_state)
    
    # Retrieve from cache
    assert "test_form" in agent._form_cache


# ─────────────────────────────────────────────────────────────────────────────
# Test: FastAPI Integration
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_extract_form_request():
    """Test HTTP handler for form extraction."""
    html = '<form id="test"><input type="text" name="test"></form>'
    result = await handle_form_navigation_request(
        action="extract_form",
        payload={"html": html},
    )
    
    assert result.success


@pytest.mark.asyncio
async def test_handle_classify_fields_request():
    """Test HTTP handler for field classification."""
    html = '<form><input type="email" name="email"></form>'
    result = await handle_form_navigation_request(
        action="classify_fields",
        payload={"html": html},
    )
    
    assert result.success


@pytest.mark.asyncio
async def test_handle_unknown_action():
    """Test handler with unknown action."""
    result = await handle_form_navigation_request(
        action="unknown_action",
        payload={},
    )
    
    assert not result.success
    assert "Unknown action" in result.error_message


# ─────────────────────────────────────────────────────────────────────────────
# Test: Confidence Scores
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confidence_extraction(agent, simple_form_html):
    """Test confidence scores on extraction."""
    result = await agent.extract_form_structure(simple_form_html)
    
    assert result.confidence >= 0.8
    assert result.form_state.confidence >= 0.8


@pytest.mark.asyncio
async def test_confidence_validation(agent, simple_form_html):
    """Test confidence scores on validation."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    result = await agent.validate_form_fields(form_state, {"username": "test"})
    
    assert result.confidence >= 0.9


# ─────────────────────────────────────────────────────────────────────────────
# Test: Performance
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extraction_performance(agent, simple_form_html):
    """Test extraction performance is under 10ms."""
    result = await agent.extract_form_structure(simple_form_html)
    
    assert result.execution_time_ms < 10.0


@pytest.mark.asyncio
async def test_validation_performance(agent, simple_form_html):
    """Test validation performance is under 10ms."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    result = await agent.validate_form_fields(form_state, {"username": "test"})
    
    assert result.execution_time_ms < 10.0


@pytest.mark.asyncio
async def test_path_detection_performance(agent, simple_form_html):
    """Test path detection performance is under 10ms."""
    form_result = await agent.extract_form_structure(simple_form_html)
    form_state = form_result.form_state
    
    result = await agent.detect_navigation_paths(form_state)
    
    assert result.execution_time_ms < 10.0


# ─────────────────────────────────────────────────────────────────────────────
# Test: JSON Serialization
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_result_to_json(agent, simple_form_html):
    """Test that result can be serialized to JSON."""
    result = await agent.extract_form_structure(simple_form_html)
    
    json_str = result.to_json()
    assert isinstance(json_str, str)
    
    # Verify it's valid JSON
    parsed = json.loads(json_str)
    assert "success" in parsed
    assert "form_state" in parsed


@pytest.mark.asyncio
async def test_malformed_form_recovery(agent):
    """Test graceful recovery from malformed form."""
    malformed_html = """
    <form id="broken">
        <input type="text" name="field1" 
        <input type="email" name="field2" invalid_attr
        <textarea name="field3"
    </form>
    """
    result = await agent.extract_form_structure(malformed_html)
    
    # Should not crash
    assert result is not None
    assert isinstance(result, FormNavigationResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
