"""
Benchmark Suite for Form Navigation Agent

Generates 30 benchmark runs with performance metrics and confidence scores.
Output: logs/form_navigator_benchmark.json
"""

import asyncio
import json
import time
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from form_navigator import FormNavigationAgent


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark Data
# ─────────────────────────────────────────────────────────────────────────────


SIMPLE_FORM = """
<form id="contact_form" name="contact">
    <input type="text" name="username" placeholder="Username" required>
    <input type="email" name="email" placeholder="Email" required>
    <input type="password" name="password" placeholder="Password" required>
    <textarea name="message" placeholder="Message"></textarea>
    <input type="submit" value="Submit">
</form>
"""

MEDIUM_FORM = """
<form id="registration" name="register">
    <fieldset id="step_1">
        <legend>Personal Info</legend>
        <input type="text" name="firstname" required>
        <input type="text" name="lastname" required>
        <input type="date" name="dob">
    </fieldset>
    <fieldset id="step_2">
        <legend>Contact</legend>
        <input type="email" name="email" required>
        <input type="tel" name="phone">
        <input type="text" name="address" required>
    </fieldset>
    <fieldset id="step_3">
        <legend>Account</legend>
        <input type="password" name="password" required>
        <input type="password" name="confirm_password" required>
        <select name="country" required>
            <option value="">Select country</option>
            <option value="us">US</option>
            <option value="uk">UK</option>
            <option value="ca">Canada</option>
        </select>
    </fieldset>
    <button type="button" name="next">Next</button>
    <button type="button" name="prev">Previous</button>
    <input type="submit" value="Register">
</form>
"""

COMPLEX_FORM = """
<form id="survey_form" name="survey">
    <input type="hidden" name="survey_id" value="12345">
    <fieldset id="section_1">
        <legend>Demographic Information</legend>
        <input type="text" name="fullname" required>
        <input type="email" name="email" required>
        <input type="number" name="age" min="18" max="120" required>
        <select name="education" required>
            <option>High School</option>
            <option>Bachelor's</option>
            <option>Master's</option>
            <option>PhD</option>
        </select>
        <input type="text" name="occupation" required>
    </fieldset>
    <fieldset id="section_2">
        <legend>Experience</legend>
        <input type="number" name="years_experience" min="0" max="50">
        <textarea name="achievements"></textarea>
        <input type="checkbox" name="certifications" value="cert1">
        <input type="checkbox" name="certifications" value="cert2">
        <input type="checkbox" name="certifications" value="cert3">
    </fieldset>
    <fieldset id="section_3">
        <legend>Preferences</legend>
        <input type="radio" name="contact_preference" value="email">
        <input type="radio" name="contact_preference" value="phone">
        <input type="radio" name="contact_preference" value="mail">
        <input type="text" name="additional_notes">
        <input type="checkbox" name="subscribe" value="yes">
    </fieldset>
    <fieldset id="section_4">
        <legend>Files</legend>
        <input type="file" name="resume" accept=".pdf,.doc,.docx">
        <input type="file" name="portfolio" accept=".zip">
    </fieldset>
    <button type="button">Previous</button>
    <button type="button">Save Draft</button>
    <button type="submit">Submit Survey</button>
</form>
"""

# Test data for validation
VALID_FIELD_DATA = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "message": "This is a test message",
}

COMPLEX_FIELD_DATA = {
    "fullname": "John Smith",
    "email": "john.smith@example.com",
    "age": "35",
    "education": "Master's",
    "occupation": "Software Engineer",
    "years_experience": "10",
    "achievements": "Led team of 5 engineers",
    "certifications": "cert1",
    "contact_preference": "email",
    "additional_notes": "Available for immediate start",
    "subscribe": "yes",
}


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark Result Model
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class BenchmarkResult:
    test_name: str
    form_size: str  # simple, medium, complex
    operation: str  # extract, validate, classify, etc.
    execution_time_ms: float
    confidence_score: float
    success: bool
    timestamp: str


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark Suite
# ─────────────────────────────────────────────────────────────────────────────


class FormNavigatorBenchmark:
    """Run comprehensive benchmarks on FormNavigationAgent."""
    
    def __init__(self, runs_per_test: int = 30):
        self.agent = FormNavigationAgent(debug=False)
        self.runs_per_test = runs_per_test
        self.results: list[BenchmarkResult] = []
    
    async def run_all_benchmarks(self) -> dict:
        """Execute all benchmark tests."""
        print("Starting Form Navigator Benchmarks...")
        print(f"Runs per test: {self.runs_per_test}")
        print("-" * 80)
        
        # Test 1: Simple form extraction (30 runs)
        await self._benchmark_simple_extraction()
        
        # Test 2: Medium form extraction
        await self._benchmark_medium_extraction()
        
        # Test 3: Complex form extraction
        await self._benchmark_complex_extraction()
        
        # Test 4: Field classification
        await self._benchmark_field_classification()
        
        # Test 5: Field validation
        await self._benchmark_field_validation()
        
        # Test 6: Navigation path detection
        await self._benchmark_path_detection()
        
        # Test 7: Multi-step flow detection
        await self._benchmark_flow_detection()
        
        # Test 8: Submission readiness assessment
        await self._benchmark_submission_readiness()
        
        # Test 9: Sequence tracing
        await self._benchmark_sequence_tracing()
        
        # Test 10: Error detection
        await self._benchmark_error_detection()
        
        # Generate summary report
        summary = self._generate_summary()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_benchmarks": len(self.results),
            "results": [asdict(r) for r in self.results],
            "summary": summary,
        }
    
    async def _benchmark_simple_extraction(self):
        """Benchmark simple form extraction."""
        print("\n🔍 Simple Form Extraction (30 runs)...")
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.extract_form_structure(SIMPLE_FORM)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="simple_form_extraction",
                form_size="simple",
                operation="extract_form_structure",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_medium_extraction(self):
        """Benchmark medium form extraction."""
        print("\n📋 Medium Form Extraction (30 runs)...")
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.extract_form_structure(MEDIUM_FORM)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="medium_form_extraction",
                form_size="medium",
                operation="extract_form_structure",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_complex_extraction(self):
        """Benchmark complex form extraction."""
        print("\n📊 Complex Form Extraction (30 runs)...")
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.extract_form_structure(COMPLEX_FORM)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="complex_form_extraction",
                form_size="complex",
                operation="extract_form_structure",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_field_classification(self):
        """Benchmark field type classification."""
        print("\n📝 Field Classification (30 runs)...")
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.classify_field_types(COMPLEX_FORM)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="field_classification",
                form_size="complex",
                operation="classify_field_types",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_field_validation(self):
        """Benchmark field validation."""
        print("\n✅ Field Validation (30 runs)...")
        
        # Extract form once
        extraction = await self.agent.extract_form_structure(SIMPLE_FORM)
        form_state = extraction.form_state
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.validate_form_fields(form_state, VALID_FIELD_DATA)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="field_validation",
                form_size="simple",
                operation="validate_form_fields",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_path_detection(self):
        """Benchmark navigation path detection."""
        print("\n🛣️  Path Detection (30 runs)...")
        
        extraction = await self.agent.extract_form_structure(MEDIUM_FORM)
        form_state = extraction.form_state
        form_state.total_steps = 3
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.detect_navigation_paths(form_state)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="path_detection",
                form_size="medium",
                operation="detect_navigation_paths",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_flow_detection(self):
        """Benchmark flow type detection."""
        print("\n🔄 Flow Detection (30 runs)...")
        
        extraction = await self.agent.extract_form_structure(MEDIUM_FORM)
        form_state = extraction.form_state
        form_state.total_steps = 3
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.detect_multi_step_flow(form_state)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="flow_detection",
                form_size="medium",
                operation="detect_multi_step_flow",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_submission_readiness(self):
        """Benchmark submission readiness assessment."""
        print("\n🚀 Submission Readiness (30 runs)...")
        
        extraction = await self.agent.extract_form_structure(SIMPLE_FORM)
        form_state = extraction.form_state
        
        # Fill required fields
        for field in form_state.current_fields:
            if field.required:
                field.value = "test_value"
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.assess_submission_readiness(form_state)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="submission_readiness",
                form_size="simple",
                operation="assess_submission_readiness",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_sequence_tracing(self):
        """Benchmark navigation sequence tracing."""
        print("\n🎯 Sequence Tracing (30 runs)...")
        
        extraction = await self.agent.extract_form_structure(MEDIUM_FORM)
        form_state = extraction.form_state
        form_state.total_steps = 3
        form_state.current_step = 0
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.trace_navigation_sequence(form_state, target_step=2)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="sequence_tracing",
                form_size="medium",
                operation="trace_navigation_sequence",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    async def _benchmark_error_detection(self):
        """Benchmark error detection."""
        print("\n⚠️  Error Detection (30 runs)...")
        
        extraction = await self.agent.extract_form_structure(COMPLEX_FORM)
        form_state = extraction.form_state
        
        for i in range(self.runs_per_test):
            start = time.perf_counter()
            result = await self.agent.detect_form_errors(form_state)
            elapsed = (time.perf_counter() - start) * 1000
            
            self.results.append(BenchmarkResult(
                test_name="error_detection",
                form_size="complex",
                operation="detect_form_errors",
                execution_time_ms=elapsed,
                confidence_score=result.confidence,
                success=result.success,
                timestamp=datetime.utcnow().isoformat(),
            ))
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/30 runs completed")
    
    def _generate_summary(self) -> dict:
        """Generate summary statistics."""
        summary_by_operation = {}
        
        for operation in set(r.operation for r in self.results):
            op_results = [r for r in self.results if r.operation == operation]
            times = [r.execution_time_ms for r in op_results]
            confidences = [r.confidence_score for r in op_results]
            
            summary_by_operation[operation] = {
                "runs": len(op_results),
                "execution_times": {
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "avg_ms": statistics.mean(times),
                    "median_ms": statistics.median(times),
                    "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
                    "p99_ms": sorted(times)[int(len(times) * 0.99)],
                },
                "confidence_scores": {
                    "min": min(confidences),
                    "max": max(confidences),
                    "avg": statistics.mean(confidences),
                    "median": statistics.median(confidences),
                },
                "success_rate": sum(1 for r in op_results if r.success) / len(op_results),
            }
        
        return {
            "by_operation": summary_by_operation,
            "total_runs": len(self.results),
            "all_under_10ms": all(r.execution_time_ms < 10.0 for r in self.results),
            "avg_confidence": statistics.mean(r.confidence_score for r in self.results),
            "success_rate": sum(1 for r in self.results if r.success) / len(self.results),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


async def main():
    """Run benchmarks and save results."""
    benchmark = FormNavigatorBenchmark(runs_per_test=30)
    
    results = await benchmark.run_all_benchmarks()
    
    # Create logs directory if needed
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Save results
    output_path = logs_dir / "form_navigator_benchmark.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    
    summary = results["summary"]
    
    print(f"\n✅ All operations under 10ms: {summary['all_under_10ms']}")
    print(f"📊 Average confidence: {summary['avg_confidence']:.2%}")
    print(f"✓ Success rate: {summary['success_rate']:.2%}")
    print(f"📈 Total benchmark runs: {summary['total_runs']}")
    
    print("\n" + "-" * 80)
    print("OPERATION PERFORMANCE:")
    print("-" * 80)
    
    for op, stats in summary["by_operation"].items():
        times = stats["execution_times"]
        conf = stats["confidence_scores"]
        
        print(f"\n{op}:")
        print(f"  Execution: {times['min_ms']:.2f}–{times['max_ms']:.2f}ms (avg {times['avg_ms']:.2f}ms, p99 {times['p99_ms']:.2f}ms)")
        print(f"  Confidence: {conf['avg']:.1%} avg (range {conf['min']:.1%}–{conf['max']:.1%})")
        print(f"  Success: {stats['success_rate']:.1%}")
    
    print("\n" + "=" * 80)
    print(f"✅ Results saved to {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
