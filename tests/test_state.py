"""Tests for src/state.py — SII Recruitment Gateway LangGraph topology."""

from __future__ import annotations

import pytest
from langgraph.graph import StateGraph

from src.state import (
    CONSENSUS_THRESHOLD,
    ISO_CONTROL_EVALUATORS,
    ISO_CONTROL_INGESTOR,
    ISO_CONTROL_RAG_ROUTER,
    ISO_CONTROL_REFLECTION,
    ISO_CONTROL_REPORT,
    MAX_REFLECTION_LOOPS,
    GraphState,
    build_graph,
    route_reflection,
)

# ── GraphState ────────────────────────────────────────────────────────────────


def test_graph_state_required_keys_present() -> None:
    """GraphState must declare all keys required by the P1 specification."""
    required_keys = {
        'transcript',
        'code_payload',
        'security_score',
        'logic_rubric',
        'audit_trace',
        'iso_controls_applied',
        'reflection_loops',
        'consensus_score',
        'candidate_id',
    }
    # GraphState inherits from dict; verify annotations carry the required names.
    annotations = GraphState.__annotations__
    missing = required_keys - set(annotations)
    assert not missing, f'Missing GraphState keys: {missing}'


def test_graph_state_iso_controls_applied_key_exists() -> None:
    """GraphState must include the iso_controls_applied field (P1 ISO update)."""
    assert 'iso_controls_applied' in GraphState.__annotations__


def test_graph_state_audit_trace_key_exists() -> None:
    """GraphState must include the audit_trace append-only log field."""
    assert 'audit_trace' in GraphState.__annotations__


# ── ISO control constants ─────────────────────────────────────────────────────


def test_iso_control_constants_are_strings() -> None:
    """All ISO control identifiers must be non-empty strings."""
    controls = [
        ISO_CONTROL_INGESTOR,
        ISO_CONTROL_RAG_ROUTER,
        ISO_CONTROL_EVALUATORS,
        ISO_CONTROL_REFLECTION,
        ISO_CONTROL_REPORT,
    ]
    for ctrl in controls:
        assert isinstance(ctrl, str), f'ISO control must be a string, got {type(ctrl)!r}'
        assert ctrl, f'ISO control must be non-empty, got {ctrl!r}'


def test_iso_control_ingestor_value() -> None:
    """Ingestor node must be governed by ISO 27001:2022 A.8.2 (Asset Classification)."""
    assert ISO_CONTROL_INGESTOR == 'A.8.2'


def test_iso_control_rag_router_value() -> None:
    """RAG-router node must be governed by ISO 27001:2022 A.8.24 (local-only crypto/RAG)."""
    assert ISO_CONTROL_RAG_ROUTER == 'A.8.24'


def test_iso_control_evaluators_value() -> None:
    """Evaluators node must be governed by ISO 27001:2022 A.8.10 (Information Deletion)."""
    assert ISO_CONTROL_EVALUATORS == 'A.8.10'


def test_iso_control_reflection_value() -> None:
    """Reflection node must be governed by ISO 27001:2022 A.5.34 (Privacy & PII)."""
    assert ISO_CONTROL_REFLECTION == 'A.5.34'


def test_iso_control_report_value() -> None:
    """Report-generator node must be governed by ISO 27001:2022 A.8.2 (CONFIDENTIAL)."""
    assert ISO_CONTROL_REPORT == 'A.8.2'


# ── Routing constants ─────────────────────────────────────────────────────────


def test_consensus_threshold_value() -> None:
    """Consensus threshold must equal 0.7 as specified in P1."""
    assert pytest.approx(0.7) == CONSENSUS_THRESHOLD


def test_max_reflection_loops_value() -> None:
    """Max reflection-loop counter must equal 2 to prevent infinite cycles."""
    assert MAX_REFLECTION_LOOPS == 2


# ── route_reflection ──────────────────────────────────────────────────────────


def test_route_reflection_below_threshold_first_loop_routes_to_evaluators() -> None:
    """Routes to evaluators when consensus < 0.7 and no loops consumed yet."""
    state = GraphState({'consensus_score': 0.5, 'reflection_loops': 0})
    assert route_reflection(state) == 'evaluators'


def test_route_reflection_below_threshold_one_loop_routes_to_evaluators() -> None:
    """Routes to evaluators when consensus < 0.7 and one loop consumed."""
    state = GraphState({'consensus_score': 0.4, 'reflection_loops': 1})
    assert route_reflection(state) == 'evaluators'


def test_route_reflection_below_threshold_max_loops_routes_to_report() -> None:
    """Routes to report_generator when consensus < 0.7 but loop limit reached."""
    state = GraphState({'consensus_score': 0.5, 'reflection_loops': MAX_REFLECTION_LOOPS})
    assert route_reflection(state) == 'report_generator'


def test_route_reflection_above_threshold_routes_to_report() -> None:
    """Routes to report_generator when consensus >= 0.7 regardless of loops."""
    state = GraphState({'consensus_score': 0.9, 'reflection_loops': 0})
    assert route_reflection(state) == 'report_generator'


def test_route_reflection_exactly_at_threshold_routes_to_report() -> None:
    """Consensus equal to threshold (0.7) is NOT below threshold — routes forward."""
    state = GraphState({'consensus_score': CONSENSUS_THRESHOLD, 'reflection_loops': 0})
    assert route_reflection(state) == 'report_generator'


def test_route_reflection_missing_keys_defaults_to_evaluators() -> None:
    """Missing state keys default to 0 and 0 loops, routing back to evaluators."""
    state = GraphState({})
    assert route_reflection(state) == 'evaluators'


def test_route_reflection_return_type_is_string() -> None:
    """route_reflection must always return a string node name."""
    state = GraphState({'consensus_score': 0.3, 'reflection_loops': 0})
    result = route_reflection(state)
    assert isinstance(result, str)


# ── build_graph ───────────────────────────────────────────────────────────────


def test_build_graph_returns_state_graph_instance() -> None:
    """build_graph must return a LangGraph StateGraph."""
    graph = build_graph()
    assert isinstance(graph, StateGraph)


def test_build_graph_contains_all_required_nodes() -> None:
    """Graph must contain all five pipeline nodes specified in P1."""
    required_nodes = {'ingestor', 'rag_router', 'evaluators', 'reflection', 'report_generator'}
    graph = build_graph()
    registered = set(graph.nodes)
    # LangGraph injects __start__ / __end__ virtual nodes; ignore those.
    pipeline_nodes = {n for n in registered if not n.startswith('__')}
    assert required_nodes <= pipeline_nodes, f'Missing nodes: {required_nodes - pipeline_nodes}'


def test_build_graph_compiles_without_error() -> None:
    """Graph must compile successfully before any node logic is attached."""
    graph = build_graph()
    compiled = graph.compile()
    assert compiled is not None


def test_build_graph_produces_independent_instances() -> None:
    """Each call to build_graph must return a fresh, independent StateGraph."""
    graph_a = build_graph()
    graph_b = build_graph()
    assert graph_a is not graph_b


def test_build_graph_conditional_edge_registered() -> None:
    """A conditional edge from reflection must be wired in the graph."""
    graph = build_graph()
    # LangGraph stores branch data keyed by source node; verify reflection has one.
    branches = graph.branches.get('reflection', {})
    assert branches, 'reflection node must have at least one conditional branch registered'
