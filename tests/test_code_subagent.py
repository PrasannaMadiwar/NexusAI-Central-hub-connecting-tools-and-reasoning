"""
Unit tests for Daytona Sandboxed Python Code Execution subagent.
Validates:
1. Lazy loading behavior (no eager connection on import).
2. End-to-end execution flow with mocked Daytona client and sandbox backend.
3. Graceful degradation when Daytona sandbox fails to initialize.
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage
from nexusai.engine.subagents.code import LazyCodeAgent, code_agent


def test_lazy_code_agent_not_initialized_on_import():
    """Verify that LazyCodeAgent does not connect to external services on instantiation."""
    agent = LazyCodeAgent()
    assert agent._agent is None


def test_lazy_code_agent_with_mocked_daytona():
    """Verify that LazyCodeAgent successfully creates sandbox and invokes deep agent with mocked Daytona."""
    mock_sandbox = MagicMock()
    mock_daytona_instance = MagicMock()
    mock_daytona_instance.create.return_value = mock_sandbox

    mock_backend = MagicMock()
    mock_inner_agent = MagicMock()
    mock_inner_agent.invoke.return_value = {
        "messages": [AIMessage(content="Result: 42\nExecuted successfully in Daytona sandbox.")]
    }

    with patch("daytona.Daytona", return_value=mock_daytona_instance), \
         patch("langchain_daytona.DaytonaSandbox", return_value=mock_backend), \
         patch("deepagents.create_deep_agent", return_value=mock_inner_agent):

        agent = LazyCodeAgent()
        result = agent.invoke({"messages": [{"role": "user", "content": "Calculate 6 * 7"}]})

        # Verify Daytona sandbox was created
        mock_daytona_instance.create.assert_called_once()
        # Verify inner agent was invoked
        mock_inner_agent.invoke.assert_called_once()
        assert "42" in result["messages"][0].content
        assert "Daytona sandbox" in result["messages"][0].content


def test_lazy_code_agent_handles_daytona_failure_gracefully():
    """Verify that when Daytona sandbox creation throws an error, a helpful error message is returned."""
    mock_daytona_instance = MagicMock()
    mock_daytona_instance.create.side_effect = ConnectionError("Could not reach Daytona server at https://daytona.api")

    with patch("daytona.Daytona", return_value=mock_daytona_instance):
        agent = LazyCodeAgent()
        result = agent.invoke({"messages": [{"role": "user", "content": "print('hello')"}]})

        assert "messages" in result
        content = result["messages"][0].content
        assert "Code execution sandbox unavailable" in content
        assert "Could not reach Daytona server" in content
