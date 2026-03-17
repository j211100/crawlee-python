"""SII Recruitment Gateway — LangGraph state schema and graph topology.

Defines :class:`GraphState`, all ISO 27001:2022 control constants, and the
cyclic Supervisor-Worker graph for the SII technical-screening pipeline.
Node *logic* is **intentionally absent** from this module; every node is
implemented in its own dedicated file under ``src/nodes/`` (P2-P5).

Classification: CONFIDENTIAL
Applicable regulations: Ley 21.180, Ley 21.663, ISO 27001:2022

ISO 27001:2022 controls anchored at this layer:
    * A.8.2  — Asset classification (state schema carries classification labels)
    * A.5.34 — Privacy and PII protection (PII-bearing fields are redaction-ready)
"""

from __future__ import annotations

import operator
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph

# ── ISO 27001:2022 control identifiers ────────────────────────────────────────
#
# Each value corresponds to the primary ISO 27001:2022 Annex A control that
# governs the respective pipeline node.  Nodes are required to append their
# control ID to ``GraphState.iso_controls_applied`` and write a structured
# entry to ``GraphState.audit_trace`` on every invocation.

ISO_CONTROL_INGESTOR: str = 'A.8.2'  # Asset Classification
ISO_CONTROL_RAG_ROUTER: str = 'A.8.24'  # Use of Cryptography (local-only RAG)
ISO_CONTROL_EVALUATORS: str = 'A.8.10'  # Information Deletion (ephemeral eval)
ISO_CONTROL_REFLECTION: str = 'A.5.34'  # Privacy and PII Protection
ISO_CONTROL_REPORT: str = 'A.8.2'  # Asset Classification (CONFIDENTIAL output)

# ── Graph routing constants ────────────────────────────────────────────────────

CONSENSUS_THRESHOLD: float = 0.7
"""Minimum weighted consensus score required to bypass re-evaluation."""

MAX_REFLECTION_LOOPS: int = 2
"""Hard cap on reflection → evaluators re-route iterations (prevents cycles)."""

# ── Routing destination literals ──────────────────────────────────────────────

_DEST_EVALUATORS: str = 'evaluators'
_DEST_REPORT: str = 'report_generator'


# ── Shared pipeline state ─────────────────────────────────────────────────────


class GraphState(dict[str, Any]):  # type: ignore[misc]
    """Shared mutable state threaded through every LangGraph node.

    Classification: CONFIDENTIAL (Ley 21.663 / ISO 27001:2022 A.8.2)

    Attributes:
        transcript: Raw or transcribed candidate speech text.  Never logged
            without redaction (ISO 27001:2022 A.5.34).
        code_payload: Candidate-submitted source code treated as **inert data**;
            never executed outside an ephemeral sandbox (ISO 27001:2022 A.8.10).
        security_score: Aggregated OWASP security evaluation score in [0.0, 1.0].
        logic_rubric: Algorithmic-complexity and architecture sub-scores keyed by
            evaluator dimension name.
        audit_trace: Append-only log of node transitions.  Each entry is a
            ``dict`` containing at minimum ``node``, ``iso_control``,
            ``timestamp``, and ``prev_hash`` (SHA-256 chain-of-trust).
        iso_controls_applied: Ordered list of ISO 27001:2022 control IDs
            applied during the current pipeline run.  Every node appends its
            primary control on entry.
        reflection_loops: Counter of reflection → evaluators re-route iterations
            performed so far.  Bounded by :data:`MAX_REFLECTION_LOOPS`.
        consensus_score: Final weighted consensus computed by the reflection node
            (security 40 %, logic 35 %, architecture 25 %).
        candidate_id: Opaque pseudonymous identifier.  Must **never** contain
            raw PII such as a RUT, name, or e-mail address.
    """

    transcript: str
    code_payload: str
    security_score: float
    logic_rubric: dict[str, Any]
    audit_trace: Annotated[list[dict[str, Any]], operator.add]
    iso_controls_applied: Annotated[list[str], operator.add]
    reflection_loops: int
    consensus_score: float
    candidate_id: str


# ── Conditional router ────────────────────────────────────────────────────────


def route_reflection(state: GraphState) -> str:
    """Choose the next node after the reflection step.

    Routes back to *evaluators* when the pipeline has not yet reached
    consensus and the re-evaluation loop limit has not been exhausted.
    Otherwise advances to *report_generator*.

    Args:
        state: Current graph state after the reflection node has executed.

    Returns:
        ``"evaluators"`` if ``consensus_score < CONSENSUS_THRESHOLD`` and
        ``reflection_loops < MAX_REFLECTION_LOOPS``; otherwise
        ``"report_generator"``.
    """
    below_threshold = float(state.get('consensus_score', 0.0)) < CONSENSUS_THRESHOLD
    loops_remaining = int(state.get('reflection_loops', 0)) < MAX_REFLECTION_LOOPS
    if below_threshold and loops_remaining:
        return _DEST_EVALUATORS
    return _DEST_REPORT


# ── Placeholder node ──────────────────────────────────────────────────────────


def _placeholder_node(_state: GraphState) -> dict[str, Any]:
    """Pass-through stub used during graph topology validation only.

    **Replace** each occurrence with the real node function imported from the
    corresponding ``src/nodes/`` module once P2-P5 are implemented.

    Args:
        _state: Current pipeline state (unused in the stub).

    Returns:
        An empty dict (no state mutation) — LangGraph merges this with the
        existing state automatically.
    """
    return {}


# ── Graph factory ─────────────────────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Construct the SII Recruitment Gateway LangGraph cyclic graph.

    Wires the Supervisor-Worker topology described in the P1 architecture
    specification.  No node *logic* is embedded here; each node is a stub
    that must be replaced when importing the real implementations from
    ``src/nodes/*``.

    Topology::

        START
          │
        ingestor       (ISO A.8.2  — asset classification)
          │
        rag_router     (ISO A.8.24 — local-only retrieval, zero network egress)
          │
        evaluators     (ISO A.8.10 — ephemeral container destruction post-eval)
          │
        reflection     (ISO A.5.34 — PII redaction before scoring)
          │◄──────────── consensus < 0.7 AND loops < MAX_REFLECTION_LOOPS
          │
        report_generator (ISO A.8.2 — CONFIDENTIAL output labelling)
          │
        END

    Conditional edge:
        ``reflection`` → ``evaluators`` when
        ``consensus_score < 0.7`` **and** ``reflection_loops < 2``.
        Otherwise ``reflection`` → ``report_generator``.

    Returns:
        A :class:`~langgraph.graph.StateGraph` instance ready to be compiled
        by calling ``.compile()`` after substituting the real node functions.

    Note:
        IMPORTANT: This module creates only the graph structure.  Do **not**
        merge node logic into this file.  The modular structure (one file per
        node under ``src/nodes/``) is required for the node-by-node
        development workflow in P2-P5.
    """
    graph: StateGraph = StateGraph(GraphState)

    # ── Register nodes ────────────────────────────────────────────────────────
    # Each entry maps node name → implementation function.
    # Swap _placeholder_node for the real function once each P prompt is done.
    graph.add_node('ingestor', _placeholder_node)  # P2
    graph.add_node('rag_router', _placeholder_node)  # P3
    graph.add_node('evaluators', _placeholder_node)  # P4
    graph.add_node('reflection', _placeholder_node)  # P5
    graph.add_node('report_generator', _placeholder_node)  # P5

    # ── Deterministic edges ───────────────────────────────────────────────────
    graph.add_edge(START, 'ingestor')
    graph.add_edge('ingestor', 'rag_router')
    graph.add_edge('rag_router', 'evaluators')
    graph.add_edge('evaluators', 'reflection')

    # ── Conditional edge: reflection → evaluators OR report_generator ─────────
    graph.add_conditional_edges(
        'reflection',
        route_reflection,
        {
            _DEST_EVALUATORS: _DEST_EVALUATORS,
            _DEST_REPORT: _DEST_REPORT,
        },
    )

    graph.add_edge('report_generator', END)

    return graph
