"""LangGraph orchestration: the four specialists fan out in parallel from
START, then fan back in to the aggregator once all four have finished."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agents import aggregator, fundamentals, risk, sentiment, technical
from agents.base import AgentResult


class ResearchState(TypedDict):
    ticker: str
    technical: AgentResult
    fundamentals: AgentResult
    sentiment: AgentResult
    risk: AgentResult
    final_report: str


def _technical_node(state: ResearchState) -> dict:
    return {"technical": technical.run(state["ticker"])}


def _fundamentals_node(state: ResearchState) -> dict:
    return {"fundamentals": fundamentals.run(state["ticker"])}


def _sentiment_node(state: ResearchState) -> dict:
    return {"sentiment": sentiment.run(state["ticker"])}


def _risk_node(state: ResearchState) -> dict:
    return {"risk": risk.run(state["ticker"])}


def _aggregator_node(state: ResearchState) -> dict:
    results = [state["technical"], state["fundamentals"], state["sentiment"], state["risk"]]
    return {"final_report": aggregator.run(state["ticker"], results)}


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("technical", _technical_node)
    graph.add_node("fundamentals", _fundamentals_node)
    graph.add_node("sentiment", _sentiment_node)
    graph.add_node("risk", _risk_node)
    graph.add_node("aggregator", _aggregator_node)

    graph.add_edge(START, "technical")
    graph.add_edge(START, "fundamentals")
    graph.add_edge(START, "sentiment")
    graph.add_edge(START, "risk")

    graph.add_edge("technical", "aggregator")
    graph.add_edge("fundamentals", "aggregator")
    graph.add_edge("sentiment", "aggregator")
    graph.add_edge("risk", "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()
