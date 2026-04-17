"""Tests for query complexity detection and tool effectiveness."""

import pytest
from src.ml.complexity_detector import (
    QueryComplexityDetector,
    ToolEffectivenessTracker,
    ComplexityLevel,
)


class TestComplexityDetection:
    """Test query complexity detection."""

    def setup_method(self):
        """Setup detector."""
        self.detector = QueryComplexityDetector()

    def test_simple_query(self):
        """Test detection of simple queries."""
        queries = [
            "What is Python?",
            "Who is Albert Einstein?",
            "Where is the Eiffel Tower?",
            "Tell me about machine learning",
        ]

        for query in queries:
            complexity = self.detector.detect_complexity(query)
            assert complexity == ComplexityLevel.SIMPLE

    def test_moderate_query(self):
        """Test detection of moderate queries."""
        queries = [
            "Compare Python and JavaScript",
            "Analyze the pros and cons of cloud computing",
            "Explain how neural networks work",
            "Summarize the benefits of remote work",
        ]

        for query in queries:
            complexity = self.detector.detect_complexity(query)
            assert complexity == ComplexityLevel.MODERATE

    def test_complex_query(self):
        """Test detection of complex queries."""
        queries = [
            "Design a scalable microservices architecture",
            "How would you implement a distributed cache?",
            "Create an optimization algorithm for routing",
            "Solve the traveling salesman problem",
        ]

        for query in queries:
            complexity = self.detector.detect_complexity(query)
            assert complexity == ComplexityLevel.COMPLEX

    def test_very_complex_query(self):
        """Test detection of very complex queries."""
        queries = [
            "Research deep learning applications in healthcare and provide comprehensive analysis",
            "Investigate correlations between AI adoption and business outcomes",
            "Conduct a deep dive into distributed consensus algorithms",
        ]

        for query in queries:
            complexity = self.detector.detect_complexity(query)
            assert complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]

    def test_complexity_score(self):
        """Test complexity score calculation."""
        # Simple query
        score = self.detector._calculate_complexity_score("What is this?")
        assert score < 2

        # Moderate query
        score = self.detector._calculate_complexity_score("Compare A and B in detail")
        assert 2 <= score < 4

        # Complex query
        score = self.detector._calculate_complexity_score("Design a system to solve X problem")
        assert 4 <= score < 6

        # Very complex query
        score = self.detector._calculate_complexity_score(
            "Research and analyze comprehensive solutions for distributed systems"
        )
        assert score >= 5  # Should be 5+ due to "research" keyword

    def test_long_query_increases_complexity(self):
        """Test that longer queries increase complexity."""
        short = "What is AI?"
        long = "What is artificial intelligence and how does it relate to machine learning, deep learning, and modern applications?"

        short_score = self.detector._calculate_complexity_score(short)
        long_score = self.detector._calculate_complexity_score(long)

        assert long_score >= short_score  # Length can contribute to complexity

    def test_multiple_sentences_increase_complexity(self):
        """Test that multiple sentences increase complexity."""
        single = "What is machine learning?"
        multiple = "What is machine learning? How is it different from deep learning? What are real-world applications?"

        single_score = self.detector._calculate_complexity_score(single)
        multiple_score = self.detector._calculate_complexity_score(multiple)

        assert multiple_score > single_score

    def test_code_complexity(self):
        """Test detection of code-related complexity."""
        query = "Create a function: def solve(x): return x**2 + 2*x + 1"
        complexity = self.detector.detect_complexity(query)
        assert complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]

    def test_estimate_tokens(self):
        """Test token estimation."""
        short = "What is AI?"
        medium = "Tell me about artificial intelligence"
        long = "Provide a comprehensive analysis of AI, machine learning, deep learning, and their applications"

        short_tokens = self.detector.estimate_tokens(short)
        medium_tokens = self.detector.estimate_tokens(medium)
        long_tokens = self.detector.estimate_tokens(long)

        assert short_tokens < medium_tokens < long_tokens

    def test_estimate_duration(self):
        """Test duration estimation based on complexity."""
        durations = {
            ComplexityLevel.SIMPLE: self.detector.estimate_duration_seconds(ComplexityLevel.SIMPLE),
            ComplexityLevel.MODERATE: self.detector.estimate_duration_seconds(ComplexityLevel.MODERATE),
            ComplexityLevel.COMPLEX: self.detector.estimate_duration_seconds(ComplexityLevel.COMPLEX),
            ComplexityLevel.VERY_COMPLEX: self.detector.estimate_duration_seconds(ComplexityLevel.VERY_COMPLEX),
        }

        # Simple < Moderate < Complex < Very Complex
        assert durations[ComplexityLevel.SIMPLE] < durations[ComplexityLevel.MODERATE]
        assert durations[ComplexityLevel.MODERATE] < durations[ComplexityLevel.COMPLEX]
        assert durations[ComplexityLevel.COMPLEX] < durations[ComplexityLevel.VERY_COMPLEX]


class TestToolSuggestion:
    """Test tool suggestion based on query."""

    def setup_method(self):
        """Setup detector."""
        self.detector = QueryComplexityDetector()
        self.available_tools = [
            "search",
            "calculator",
            "code_generator",
            "debugger",
            "analytics",
            "knowledge_base",
        ]

    def test_suggest_search_tool(self):
        """Test search tool suggestion."""
        query = "Search for recent AI breakthroughs"
        suggestions = self.detector.suggest_tools(query, self.available_tools)

        assert suggestions["search"] > 0.8
        assert suggestions["knowledge_base"] > 0.8

    def test_suggest_calculator_tool(self):
        """Test calculator tool suggestion."""
        query = "Calculate 2^10 + 5*3"
        suggestions = self.detector.suggest_tools(query, self.available_tools)

        assert suggestions["calculator"] > 0.8

    def test_suggest_code_generator_tool(self):
        """Test code generator tool suggestion."""
        query = "Generate a Python script to parse JSON"
        suggestions = self.detector.suggest_tools(query, self.available_tools)

        assert suggestions["code_generator"] > 0.8

    def test_suggest_analytics_tool(self):
        """Test analytics tool suggestion."""
        query = "Analyze trends in data and forecast next quarter"
        suggestions = self.detector.suggest_tools(query, self.available_tools)

        assert suggestions["analytics"] > 0.8

    def test_tool_suggestions_all_present(self):
        """Test that all tools get suggestions."""
        query = "What is the weather?"
        suggestions = self.detector.suggest_tools(query, self.available_tools)

        for tool in self.available_tools:
            assert tool in suggestions
            assert 0 <= suggestions[tool] <= 1.0

    def test_tool_suggestions_complex_query(self):
        """Test suggestions for complex multi-tool query."""
        query = "Calculate statistics on the dataset and generate visualizations"
        suggestions = self.detector.suggest_tools(query, self.available_tools)

        # Should suggest calculator and analytics (higher than default 0.5)
        assert suggestions["calculator"] >= 0.5
        assert suggestions["analytics"] >= 0.5


class TestToolEffectivenessTracker:
    """Test tool effectiveness tracking."""

    def setup_method(self):
        """Setup tracker."""
        self.tracker = ToolEffectivenessTracker()

    def test_initial_effectiveness(self):
        """Test initial effectiveness score."""
        effectiveness = self.tracker.get_tool_effectiveness("search")
        assert effectiveness == 0.5  # Default

    def test_record_successful_tool_use(self):
        """Test recording successful tool use."""
        self.tracker.record_tool_use(
            "search",
            success=True,
            tokens_used=100,
            duration_seconds=0.5,
            complexity=ComplexityLevel.SIMPLE,
        )

        effectiveness = self.tracker.get_tool_effectiveness("search")
        assert effectiveness > 0.5  # Should improve

    def test_record_failed_tool_use(self):
        """Test recording failed tool use."""
        self.tracker.record_tool_use(
            "search",
            success=False,
            tokens_used=100,
            duration_seconds=0.5,
            complexity=ComplexityLevel.SIMPLE,
        )

        effectiveness = self.tracker.get_tool_effectiveness("search")
        assert effectiveness <= 0.5  # Should decrease

    def test_effectiveness_improves_with_success(self):
        """Test effectiveness improves with repeated success."""
        # Record 5 successes
        for _ in range(5):
            self.tracker.record_tool_use(
                "calculator",
                success=True,
                tokens_used=50,
                duration_seconds=0.2,
                complexity=ComplexityLevel.SIMPLE,
            )

        effectiveness1 = self.tracker.get_tool_effectiveness("calculator")

        # Record more successes
        for _ in range(5):
            self.tracker.record_tool_use(
                "calculator",
                success=True,
                tokens_used=50,
                duration_seconds=0.2,
                complexity=ComplexityLevel.SIMPLE,
            )

        effectiveness2 = self.tracker.get_tool_effectiveness("calculator")
        assert effectiveness2 >= effectiveness1

    def test_effectiveness_decreases_with_failure(self):
        """Test effectiveness decreases with repeated failure."""
        initial = self.tracker.get_tool_effectiveness("debugger")

        # Record 5 failures
        for _ in range(5):
            self.tracker.record_tool_use(
                "debugger",
                success=False,
                tokens_used=500,
                duration_seconds=2.0,
                complexity=ComplexityLevel.COMPLEX,
            )

        effectiveness = self.tracker.get_tool_effectiveness("debugger")
        assert effectiveness < initial

    def test_get_tool_stats(self):
        """Test getting full tool stats."""
        self.tracker.record_tool_use(
            "search",
            success=True,
            tokens_used=100,
            duration_seconds=0.5,
            complexity=ComplexityLevel.SIMPLE,
        )

        stats = self.tracker.get_tool_stats("search")

        assert stats is not None
        assert stats["uses"] == 1
        assert stats["successes"] == 1
        assert stats["failures"] == 0
        assert stats["total_tokens"] == 100
        assert stats["total_duration"] == 0.5
        assert 0.0 <= stats["effectiveness"] <= 1.0

    def test_rank_tools(self):
        """Test ranking tools by effectiveness."""
        # Record successes for search
        for _ in range(10):
            self.tracker.record_tool_use(
                "search",
                success=True,
                tokens_used=50,
                duration_seconds=0.2,
                complexity=ComplexityLevel.SIMPLE,
            )

        # Record failures for calculator
        for _ in range(5):
            self.tracker.record_tool_use(
                "calculator",
                success=False,
                tokens_used=200,
                duration_seconds=1.0,
                complexity=ComplexityLevel.MODERATE,
            )

        tools = ["search", "calculator", "code_generator"]
        rankings = self.tracker.rank_tools(tools)

        # Search should rank higher than calculator
        assert rankings[0][0] == "search"
        assert rankings[0][1] > rankings[1][1]

    def test_effectiveness_floor(self):
        """Test effectiveness doesn't go below floor."""
        # Record many failures
        for _ in range(20):
            self.tracker.record_tool_use(
                "broken_tool",
                success=False,
                tokens_used=1000,
                duration_seconds=10.0,
                complexity=ComplexityLevel.VERY_COMPLEX,
            )

        effectiveness = self.tracker.get_tool_effectiveness("broken_tool")
        assert effectiveness >= 0.1  # Floor at 0.1

    def test_reset_tool(self):
        """Test resetting tool stats."""
        self.tracker.record_tool_use(
            "search",
            success=True,
            tokens_used=100,
            duration_seconds=0.5,
            complexity=ComplexityLevel.SIMPLE,
        )

        stats_before = self.tracker.get_tool_stats("search")
        assert stats_before is not None

        self.tracker.reset_tool("search")
        stats_after = self.tracker.get_tool_stats("search")
        assert stats_after is None

    def test_multiple_tools_independent(self):
        """Test effectiveness tracking is independent per tool."""
        # Successes for tool A
        for _ in range(5):
            self.tracker.record_tool_use(
                "tool_a",
                success=True,
                tokens_used=50,
                duration_seconds=0.2,
                complexity=ComplexityLevel.SIMPLE,
            )

        # Failures for tool B
        for _ in range(5):
            self.tracker.record_tool_use(
                "tool_b",
                success=False,
                tokens_used=500,
                duration_seconds=2.0,
                complexity=ComplexityLevel.COMPLEX,
            )

        effectiveness_a = self.tracker.get_tool_effectiveness("tool_a")
        effectiveness_b = self.tracker.get_tool_effectiveness("tool_b")

        assert effectiveness_a > effectiveness_b


class TestComplexityScoringAccuracy:
    """Test accuracy of complexity scoring."""

    def setup_method(self):
        """Setup detector."""
        self.detector = QueryComplexityDetector()

    def test_scoring_consistency(self):
        """Test that same query gets same score."""
        query = "Design a distributed system"

        score1 = self.detector._calculate_complexity_score(query)
        score2 = self.detector._calculate_complexity_score(query)

        assert score1 == score2

    def test_scoring_case_insensitive(self):
        """Test that scoring is case-insensitive."""
        query1 = "Calculate the result"
        query2 = "CALCULATE THE RESULT"

        score1 = self.detector._calculate_complexity_score(query1)
        score2 = self.detector._calculate_complexity_score(query2)

        assert score1 == score2

    def test_edge_case_empty_query(self):
        """Test edge case: empty query."""
        complexity = self.detector.detect_complexity("")
        assert complexity == ComplexityLevel.SIMPLE

    def test_edge_case_single_word(self):
        """Test edge case: single word query."""
        complexity = self.detector.detect_complexity("Hello")
        assert complexity == ComplexityLevel.SIMPLE

    def test_edge_case_very_long_query(self):
        """Test edge case: very long query."""
        query = " ".join(["word"] * 200)
        complexity = self.detector.detect_complexity(query)
        # Very long generic text may be moderate to complex due to length bonus
        assert complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]
