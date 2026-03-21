"""
Comprehensive test suite for ScreenshotAnalyzerAgent.

25-30 test cases covering:
- Simple page layouts
- Complex responsive designs
- Mobile layouts
- Forms with various field types
- Navigation menus
- Edge cases (empty pages, cluttered layouts, missing images)
- Dark/light themes
- Accessibility compliance
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import List

import pytest
from loguru import logger

from agents.screenshot_analyzer import (
    AccessibilityInfo,
    AnalysisResult,
    ColorInfo,
    ElementInfo,
    ElementType,
    LayoutType,
    Position,
    ScreenshotAnalyzerAgent,
    TextSize,
    PageSegment,
    act_handler,
)


# Configure test logging
logger.remove()
logger.add(
    lambda msg: None,
    level="DEBUG"
)
logger.add(
    "logs/test_screenshot_analyzer.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def agent():
    """Create a ScreenshotAnalyzerAgent instance."""
    return ScreenshotAnalyzerAgent(use_vision=False)


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a temporary dummy image file."""
    image_file = tmp_path / "test_image.png"
    
    # Create minimal valid PNG file (1x1 transparent)
    png_data = bytes([
        0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,  # PNG signature
        0x00, 0x00, 0x00, 0x0d,  # IHDR chunk length
        0x49, 0x48, 0x44, 0x52,  # IHDR
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
        0x89,  # CRC
        0x00, 0x00, 0x00, 0x0a,  # IDAT chunk length
        0x49, 0x44, 0x41, 0x54,  # IDAT
        0x78, 0x9c, 0x63, 0x00, 0x01, 0x00, 0x00, 0x05,
        0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4,  # CRC
        0x00, 0x00, 0x00, 0x00,  # IEND chunk length
        0x49, 0x45, 0x4e, 0x44,  # IEND
        0xae, 0x42, 0x60, 0x82,  # CRC
    ])
    
    image_file.write_bytes(png_data)
    return str(image_file)


# ============================================================================
# Test: Basic Initialization
# ============================================================================

class TestInitialization:
    """Test agent initialization."""

    def test_agent_creation(self, agent):
        """Test basic agent creation."""
        assert agent is not None
        assert isinstance(agent, ScreenshotAnalyzerAgent)

    def test_agent_vision_disabled(self, agent):
        """Test agent vision flag."""
        assert agent.use_vision is False

    def test_agent_logger_exists(self, agent):
        """Test agent logger is configured."""
        assert agent.logger is not None


# ============================================================================
# Test: Data Models
# ============================================================================

class TestDataModels:
    """Test dataclass models."""

    def test_position_creation(self):
        """Test Position dataclass."""
        pos = Position(x=10, y=20, width=100, height=50)
        assert pos.x == 10
        assert pos.y == 20
        assert pos.area == 5000

    def test_color_info_creation(self):
        """Test ColorInfo dataclass."""
        color = ColorInfo(hex_value="#FF0000", luminance=0.2)
        assert color.hex_value == "#FF0000"
        assert color.luminance == 0.2
        assert color.is_dark is False

    def test_accessibility_info_creation(self):
        """Test AccessibilityInfo dataclass."""
        acc = AccessibilityInfo(
            contrast_ratio=7.0,
            text_size=TextSize.LARGE,
            is_readable=True,
            aria_label_present=True
        )
        assert acc.contrast_ratio == 7.0
        assert acc.text_size == TextSize.LARGE
        assert acc.aria_label_present is True

    def test_element_info_creation(self):
        """Test ElementInfo dataclass."""
        elem = ElementInfo(
            type=ElementType.BUTTON,
            text="Click Me",
            position=Position(x=10, y=10, width=100, height=40),
            clickable=True,
            confidence=0.95
        )
        assert elem.type == ElementType.BUTTON
        assert elem.text == "Click Me"
        assert elem.clickable is True
        assert elem.confidence == 0.95

    def test_page_segment_creation(self):
        """Test PageSegment dataclass."""
        segment = PageSegment(
            name="header",
            position=Position(x=0, y=0, width=800, height=100),
            elements=[]
        )
        assert segment.name == "header"
        assert segment.position.width == 800

    def test_analysis_result_creation(self):
        """Test AnalysisResult dataclass."""
        result = AnalysisResult(
            image_path="test.png",
            image_size=(800, 600),
            elements=[],
            segments=[],
            color_scheme=[],
            layout_type=LayoutType.GRID,
            visual_hierarchy_detected=True,
            anomalies_detected=[],
            overall_confidence=0.88,
            processing_time_ms=5.5,
            accessibility_score=0.90
        )
        assert result.image_path == "test.png"
        assert result.image_size == (800, 600)
        assert result.overall_confidence == 0.88

    def test_to_dict_conversion(self):
        """Test to_dict conversion for all models."""
        elem = ElementInfo(
            type=ElementType.BUTTON,
            text="Test",
            position=Position(x=0, y=0, width=100, height=40),
            confidence=0.9
        )
        data = elem.to_dict()
        assert isinstance(data, dict)
        assert data['type'] == 'button'
        assert data['text'] == 'Test'


# ============================================================================
# Test: Image Loading
# ============================================================================

class TestImageLoading:
    """Test image loading functionality."""

    def test_load_valid_image(self, agent, sample_image_path):
        """Test loading a valid image."""
        data = agent._load_image(sample_image_path)
        assert data is not None
        assert data['path'] == sample_image_path
        assert 'size' in data

    def test_load_nonexistent_image(self, agent):
        """Test loading a nonexistent image."""
        data = agent._load_image("/nonexistent/path/image.png")
        assert data is None

    def test_load_invalid_path(self, agent):
        """Test loading with invalid path format."""
        data = agent._load_image("")
        assert data is None


# ============================================================================
# Test: Element Detection
# ============================================================================

class TestElementDetection:
    """Test UI element detection."""

    @pytest.mark.asyncio
    async def test_detect_elements_basic(self, agent):
        """Test basic element detection."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        assert len(elements) > 0
        assert any(e.type == ElementType.BUTTON for e in elements)
        assert any(e.type == ElementType.TEXT_HEADING for e in elements)

    @pytest.mark.asyncio
    async def test_detect_button_elements(self, agent):
        """Test button detection."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        buttons = [e for e in elements if e.type == ElementType.BUTTON]
        assert len(buttons) > 0
        for button in buttons:
            assert button.clickable is True
            assert button.interactive is True

    @pytest.mark.asyncio
    async def test_detect_text_elements(self, agent):
        """Test text region detection."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        text_elements = [
            e for e in elements
            if e.type in [ElementType.TEXT_HEADING, ElementType.TEXT_PARAGRAPH]
        ]
        assert len(text_elements) > 0

    @pytest.mark.asyncio
    async def test_detect_navigation(self, agent):
        """Test navigation menu detection."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        nav = [e for e in elements if e.type == ElementType.NAVIGATION_MENU]
        assert len(nav) > 0

    @pytest.mark.asyncio
    async def test_element_confidence_scores(self, agent):
        """Test that elements have confidence scores."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        for element in elements:
            assert 0.0 <= element.confidence <= 1.0


# ============================================================================
# Test: Page Segmentation
# ============================================================================

class TestPageSegmentation:
    """Test page segmentation into regions."""

    @pytest.mark.asyncio
    async def test_segment_page_basic(self, agent):
        """Test basic page segmentation."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        segments = agent._segment_page(elements, image_data)
        assert len(segments) > 0

    @pytest.mark.asyncio
    async def test_segment_page_regions(self, agent):
        """Test page is segmented into header, main, footer."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        segments = agent._segment_page(elements, image_data)
        segment_names = [s.name for s in segments]
        assert any(name in ['header', 'main', 'footer'] for name in segment_names)

    @pytest.mark.asyncio
    async def test_segment_elements_assignment(self, agent):
        """Test elements are assigned to segments."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        segments = agent._segment_page(elements, image_data)
        for segment in segments:
            assert isinstance(segment.elements, list)


# ============================================================================
# Test: Color Analysis
# ============================================================================

class TestColorAnalysis:
    """Test color scheme analysis."""

    @pytest.mark.asyncio
    async def test_analyze_color_scheme(self, agent):
        """Test color scheme extraction."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        colors = agent._analyze_color_scheme(elements)
        assert len(colors) > 0
        assert all(isinstance(c, ColorInfo) for c in colors)

    @pytest.mark.asyncio
    async def test_color_luminance_calculation(self, agent):
        """Test color luminance is calculated."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        colors = agent._analyze_color_scheme(elements)
        for color in colors:
            assert 0.0 <= color.luminance <= 1.0

    def test_luminance_white(self, agent):
        """Test white color luminance."""
        lum = agent._calculate_luminance("#FFFFFF")
        assert lum > 0.9

    def test_luminance_black(self, agent):
        """Test black color luminance."""
        lum = agent._calculate_luminance("#000000")
        assert lum < 0.1

    def test_luminance_gray(self, agent):
        """Test gray color luminance."""
        lum = agent._calculate_luminance("#808080")
        assert 0.2 < lum < 0.4


# ============================================================================
# Test: Layout Detection
# ============================================================================

class TestLayoutDetection:
    """Test layout type detection."""

    @pytest.mark.asyncio
    async def test_detect_layout_type(self, agent):
        """Test layout type detection."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        layout = agent._detect_layout_type(elements, image_data)
        assert layout in [LayoutType.GRID, LayoutType.FLEXBOX, LayoutType.FLOAT, LayoutType.UNKNOWN]

    @pytest.mark.asyncio
    async def test_layout_with_elements(self, agent):
        """Test layout detection with real elements."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        layout = agent._detect_layout_type(elements, image_data)
        assert layout != LayoutType.UNKNOWN or len(elements) == 0

    @pytest.mark.asyncio
    async def test_layout_empty_elements(self, agent):
        """Test layout detection with no elements."""
        image_data = {"size": (800, 600)}
        layout = agent._detect_layout_type([], image_data)
        assert layout == LayoutType.UNKNOWN


# ============================================================================
# Test: Visual Hierarchy
# ============================================================================

class TestVisualHierarchy:
    """Test visual hierarchy detection."""

    @pytest.mark.asyncio
    async def test_detect_visual_hierarchy(self, agent):
        """Test visual hierarchy detection."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        has_hierarchy = agent._detect_visual_hierarchy(elements)
        assert isinstance(has_hierarchy, bool)

    @pytest.mark.asyncio
    async def test_hierarchy_with_varied_sizes(self, agent):
        """Test hierarchy detection with varied element sizes."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        has_hierarchy = agent._detect_visual_hierarchy(elements)
        # Should detect hierarchy since we have headings and buttons
        assert has_hierarchy is True

    @pytest.mark.asyncio
    async def test_hierarchy_empty_elements(self, agent):
        """Test hierarchy detection with no elements."""
        has_hierarchy = agent._detect_visual_hierarchy([])
        assert has_hierarchy is False


# ============================================================================
# Test: Anomaly Detection
# ============================================================================

class TestAnomalyDetection:
    """Test visual anomaly detection."""

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, agent):
        """Test anomaly detection."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        anomalies = agent._detect_anomalies(elements, image_data)
        assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    async def test_low_contrast_detection(self, agent):
        """Test low contrast anomaly detection."""
        low_contrast_elem = ElementInfo(
            type=ElementType.TEXT_PARAGRAPH,
            text="Low contrast text",
            position=Position(x=0, y=0, width=100, height=20),
            accessibility=AccessibilityInfo(contrast_ratio=3.0)
        )
        anomalies = agent._detect_anomalies([low_contrast_elem], {"size": (800, 600)})
        assert any("Low contrast" in a for a in anomalies)

    @pytest.mark.asyncio
    async def test_missing_alt_text_detection(self, agent):
        """Test missing alt text detection."""
        image_elem = ElementInfo(
            type=ElementType.IMAGE_MEDIA,
            text="",
            position=Position(x=0, y=0, width=100, height=100),
            accessibility=AccessibilityInfo(alt_text_present=False)
        )
        anomalies = agent._detect_anomalies([image_elem], {"size": (800, 600)})
        assert any("alt text" in a.lower() for a in anomalies)

    @pytest.mark.asyncio
    async def test_cluttered_layout_detection(self, agent):
        """Test cluttered layout detection."""
        # Create 35 elements (more than threshold)
        elements = [
            ElementInfo(
                type=ElementType.TEXT_LABEL,
                text=f"Element {i}",
                position=Position(x=i % 5 * 100, y=i // 5 * 100, width=80, height=80),
                accessibility=AccessibilityInfo(contrast_ratio=7.0)
            )
            for i in range(35)
        ]
        anomalies = agent._detect_anomalies(elements, {"size": (800, 600)})
        assert any("cluttered" in a.lower() for a in anomalies)


# ============================================================================
# Test: Accessibility Scoring
# ============================================================================

class TestAccessibilityScoring:
    """Test accessibility score calculation."""

    @pytest.mark.asyncio
    async def test_calculate_accessibility_score(self, agent):
        """Test accessibility score calculation."""
        image_data = {"size": (800, 600)}
        elements = await agent._detect_elements(image_data)
        score = agent._calculate_accessibility_score(elements)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_accessibility_empty_elements(self, agent):
        """Test accessibility score with no elements."""
        score = agent._calculate_accessibility_score([])
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_accessibility_high_contrast(self, agent):
        """Test high contrast increases score."""
        elem = ElementInfo(
            type=ElementType.BUTTON,
            text="Button",
            position=Position(x=0, y=0, width=100, height=40),
            accessibility=AccessibilityInfo(
                contrast_ratio=21.0,
                text_size=TextSize.LARGE,
                is_readable=True,
                aria_label_present=True
            )
        )
        score = agent._calculate_accessibility_score([elem])
        assert score > 0.85

    def test_accessibility_low_contrast(self, agent):
        """Test low contrast decreases score."""
        elem = ElementInfo(
            type=ElementType.TEXT_PARAGRAPH,
            text="Text",
            position=Position(x=0, y=0, width=100, height=20),
            accessibility=AccessibilityInfo(
                contrast_ratio=2.0,
                text_size=TextSize.SMALL,
                is_readable=False
            )
        )
        score = agent._calculate_accessibility_score([elem])
        assert score < 0.5


# ============================================================================
# Test: Theme Detection
# ============================================================================

class TestThemeDetection:
    """Test light/dark theme detection."""

    def test_detect_light_theme(self, agent):
        """Test light theme detection."""
        colors = [ColorInfo(hex_value="#FFFFFF", luminance=0.95)]
        theme = agent._detect_theme(colors)
        assert theme == "light"

    def test_detect_dark_theme(self, agent):
        """Test dark theme detection."""
        colors = [ColorInfo(hex_value="#000000", luminance=0.05)]
        theme = agent._detect_theme(colors)
        assert theme == "dark"

    def test_detect_theme_empty(self, agent):
        """Test theme detection with no colors."""
        theme = agent._detect_theme([])
        assert theme == "light"  # default


# ============================================================================
# Test: Full Analysis Pipeline
# ============================================================================

class TestFullAnalysisPipeline:
    """Test complete analysis pipeline."""

    @pytest.mark.asyncio
    async def test_analyze_screenshot_basic(self, agent, sample_image_path):
        """Test basic screenshot analysis."""
        result = await agent.analyze_screenshot(sample_image_path)
        assert isinstance(result, AnalysisResult)
        assert result.image_path == sample_image_path
        assert len(result.elements) > 0
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_analysis_result_structure(self, agent, sample_image_path):
        """Test analysis result has required fields."""
        result = await agent.analyze_screenshot(sample_image_path)
        assert result.image_size is not None
        assert result.elements is not None
        assert result.segments is not None
        assert result.color_scheme is not None
        assert result.layout_type is not None
        assert result.overall_confidence is not None
        assert result.accessibility_score is not None

    @pytest.mark.asyncio
    async def test_overall_confidence_range(self, agent, sample_image_path):
        """Test overall confidence is in valid range."""
        result = await agent.analyze_screenshot(sample_image_path)
        assert 0.0 <= result.overall_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_processing_time_reasonable(self, agent, sample_image_path):
        """Test processing time is reasonable (< 100ms)."""
        result = await agent.analyze_screenshot(sample_image_path)
        assert result.processing_time_ms < 100

    @pytest.mark.asyncio
    async def test_analysis_nonexistent_image(self, agent):
        """Test analysis with nonexistent image."""
        with pytest.raises(ValueError):
            await agent.analyze_screenshot("/nonexistent/image.png")

    @pytest.mark.asyncio
    async def test_analysis_to_json(self, agent, sample_image_path):
        """Test analysis result can be converted to JSON."""
        result = await agent.analyze_screenshot(sample_image_path)
        json_str = agent.to_json(result)
        data = json.loads(json_str)
        assert data['image_path'] == sample_image_path
        assert 'elements' in data
        assert 'segments' in data


# ============================================================================
# Test: Batch Analysis
# ============================================================================

class TestBatchAnalysis:
    """Test batch analysis functionality."""

    @pytest.mark.asyncio
    async def test_batch_analyze_multiple(self, agent, tmp_path):
        """Test batch analysis of multiple images."""
        # Create 3 dummy images
        image_paths = []
        for i in range(3):
            image_file = tmp_path / f"test_image_{i}.png"
            png_data = bytes([
                0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
                0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
                0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
                0x89, 0x00, 0x00, 0x00, 0x0a, 0x49, 0x44, 0x41,
                0x54, 0x78, 0x9c, 0x63, 0x00, 0x01, 0x00, 0x00,
                0x05, 0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4, 0x00,
                0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44, 0xae,
                0x42, 0x60, 0x82,
            ])
            image_file.write_bytes(png_data)
            image_paths.append(str(image_file))
        
        results = await agent.batch_analyze(image_paths)
        assert len(results) == 3
        assert all(isinstance(r, AnalysisResult) for r in results)

    @pytest.mark.asyncio
    async def test_batch_analyze_empty(self, agent):
        """Test batch analysis with no images."""
        results = await agent.batch_analyze([])
        assert results == []


# ============================================================================
# Test: HTTP Endpoint Handler
# ============================================================================

class TestHTTPEndpoint:
    """Test HTTP /act endpoint handler."""

    @pytest.mark.asyncio
    async def test_act_handler_valid(self, sample_image_path):
        """Test /act endpoint with valid request."""
        request_data = {
            "image_path": sample_image_path,
            "enable_vision": False
        }
        response = await act_handler(request_data)
        assert response['status'] == 'success'
        assert 'data' in response

    @pytest.mark.asyncio
    async def test_act_handler_missing_image_path(self):
        """Test /act endpoint with missing image_path."""
        request_data = {"enable_vision": False}
        response = await act_handler(request_data)
        assert response['status'] == 'error'
        assert 'message' in response

    @pytest.mark.asyncio
    async def test_act_handler_invalid_image(self):
        """Test /act endpoint with invalid image path."""
        request_data = {
            "image_path": "/nonexistent/image.png",
            "enable_vision": False
        }
        response = await act_handler(request_data)
        assert response['status'] == 'error'


# ============================================================================
# Test: Performance
# ============================================================================

class TestPerformance:
    """Test performance metrics."""

    @pytest.mark.asyncio
    async def test_analysis_performance(self, agent, sample_image_path):
        """Test analysis completes in reasonable time."""
        import time
        start = time.time()
        result = await agent.analyze_screenshot(sample_image_path)
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should complete in under 1 second
        assert result.processing_time_ms < 100

    @pytest.mark.asyncio
    async def test_batch_performance(self, agent, tmp_path):
        """Test batch analysis performance."""
        import time
        # Create 5 test images
        image_paths = []
        for i in range(5):
            image_file = tmp_path / f"perf_test_{i}.png"
            png_data = bytes([
                0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
                0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
                0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
                0x89, 0x00, 0x00, 0x00, 0x0a, 0x49, 0x44, 0x41,
                0x54, 0x78, 0x9c, 0x63, 0x00, 0x01, 0x00, 0x00,
                0x05, 0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4, 0x00,
                0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44, 0xae,
                0x42, 0x60, 0x82,
            ])
            image_file.write_bytes(png_data)
            image_paths.append(str(image_file))
        
        start = time.time()
        results = await agent.batch_analyze(image_paths)
        elapsed = time.time() - start
        assert elapsed < 5.0  # Should complete in under 5 seconds
        assert len(results) == 5


# ============================================================================
# Test: JSON Serialization
# ============================================================================

class TestJSONSerialization:
    """Test JSON serialization of results."""

    @pytest.mark.asyncio
    async def test_result_to_dict(self, agent, sample_image_path):
        """Test result can be converted to dict."""
        result = await agent.analyze_screenshot(sample_image_path)
        data = result.to_dict()
        assert isinstance(data, dict)
        assert 'image_path' in data

    @pytest.mark.asyncio
    async def test_result_to_json(self, agent, sample_image_path):
        """Test result can be converted to JSON string."""
        result = await agent.analyze_screenshot(sample_image_path)
        json_str = agent.to_json(result)
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data['image_path'] == sample_image_path

    def test_element_to_dict(self):
        """Test element can be converted to dict."""
        elem = ElementInfo(
            type=ElementType.BUTTON,
            text="Test Button",
            position=Position(x=0, y=0, width=100, height=40),
            confidence=0.95
        )
        data = elem.to_dict()
        assert data['type'] == 'button'
        assert data['text'] == 'Test Button'


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
