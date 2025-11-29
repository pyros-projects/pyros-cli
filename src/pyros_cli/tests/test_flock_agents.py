"""Tests for flock agent implementations.

These tests verify the artifact models and agent registration
for the new blackboard-based architecture.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from pyros_cli.models.flock_artifacts import PromptEnhanceRequest, EnhancedPrompt


class TestPromptEnhanceRequest:
    """Tests for PromptEnhanceRequest artifact model."""
    
    def test_creates_valid_request_with_all_fields(self):
        """Test creating a request with all fields populated."""
        request = PromptEnhanceRequest(
            user_prompt="A cat sitting on a windowsill",
            user_instruction="Make it more artistic and detailed"
        )
        assert request.user_prompt == "A cat sitting on a windowsill"
        assert request.user_instruction == "Make it more artistic and detailed"
    
    def test_creates_request_with_default_instruction(self):
        """Test that user_instruction defaults to empty string."""
        request = PromptEnhanceRequest(
            user_prompt="A sunset over mountains"
        )
        assert request.user_prompt == "A sunset over mountains"
        assert request.user_instruction == ""
    
    def test_request_serialization(self):
        """Test that the model serializes correctly."""
        request = PromptEnhanceRequest(
            user_prompt="Test prompt",
            user_instruction="Test instruction"
        )
        data = request.model_dump()
        assert data["user_prompt"] == "Test prompt"
        assert data["user_instruction"] == "Test instruction"


class TestEnhancedPrompt:
    """Tests for EnhancedPrompt artifact model."""
    
    def test_creates_valid_response(self):
        """Test creating an enhanced prompt response."""
        response = EnhancedPrompt(
            enhanced_prompt="A fluffy orange tabby cat bathed in golden afternoon light",
            original_prompt="A cat"
        )
        assert "fluffy" in response.enhanced_prompt
        assert response.original_prompt == "A cat"
    
    def test_creates_response_with_default_original(self):
        """Test that original_prompt defaults to empty string."""
        response = EnhancedPrompt(
            enhanced_prompt="Enhanced prompt text here"
        )
        assert response.enhanced_prompt == "Enhanced prompt text here"
        assert response.original_prompt == ""
    
    def test_response_serialization(self):
        """Test that the model serializes correctly."""
        response = EnhancedPrompt(
            enhanced_prompt="Enhanced text",
            original_prompt="Original text"
        )
        data = response.model_dump()
        assert data["enhanced_prompt"] == "Enhanced text"
        assert data["original_prompt"] == "Original text"


class TestEnhanceAgentRegistration:
    """Tests for enhance_agent registration."""
    
    def test_register_enhance_agent_calls_builder_methods(self):
        """Test that registration uses the correct builder pattern."""
        from pyros_cli.agents.enhance_agent import register_enhance_agent
        
        # Create mock flock with builder chain
        mock_flock = MagicMock()
        mock_agent_builder = MagicMock()
        mock_description_builder = MagicMock()
        mock_consumes_builder = MagicMock()
        
        mock_flock.agent.return_value = mock_agent_builder
        mock_agent_builder.description.return_value = mock_description_builder
        mock_description_builder.consumes.return_value = mock_consumes_builder
        mock_consumes_builder.publishes.return_value = MagicMock()
        
        # Register the agent
        register_enhance_agent(mock_flock)
        
        # Verify the builder chain was called correctly
        mock_flock.agent.assert_called_once_with("enhance_agent")
        mock_agent_builder.description.assert_called_once()
        mock_description_builder.consumes.assert_called_once_with(PromptEnhanceRequest)
        mock_consumes_builder.publishes.assert_called_once_with(EnhancedPrompt)


class TestOrchestratorAgentRegistration:
    """Tests for orchestrator_agent registration."""
    
    def test_register_orchestrator_agent_without_tools(self):
        """Test registration without tools."""
        from pyros_cli.agents.orchestrator_agent import register_orchestrator_agent
        
        mock_flock = MagicMock()
        mock_builder = MagicMock()
        mock_flock.agent.return_value = mock_builder
        mock_builder.description.return_value = mock_builder
        mock_builder.consumes.return_value = mock_builder
        mock_builder.publishes.return_value = mock_builder
        
        register_orchestrator_agent(mock_flock)
        
        mock_flock.agent.assert_called_once_with("orchestrator_agent")
        mock_builder.with_tools.assert_not_called()
    
    def test_register_orchestrator_agent_with_tools(self):
        """Test registration with tools."""
        from pyros_cli.agents.orchestrator_agent import register_orchestrator_agent
        
        mock_flock = MagicMock()
        mock_builder = MagicMock()
        mock_flock.agent.return_value = mock_builder
        mock_builder.description.return_value = mock_builder
        mock_builder.consumes.return_value = mock_builder
        mock_builder.publishes.return_value = mock_builder
        
        def dummy_tool():
            pass
        
        register_orchestrator_agent(mock_flock, tools=[dummy_tool])
        
        mock_builder.with_tools.assert_called_once_with([dummy_tool])


class TestFlockHandler:
    """Tests for flock_handler module."""
    
    @pytest.mark.asyncio
    async def test_run_flock_async_returns_enhanced_prompt(self):
        """Test that run_flock_async orchestrates correctly and returns result."""
        from pyros_cli.agents.flock_handler import run_flock_async
        
        with patch('pyros_cli.agents.flock_handler.Flock') as MockFlock:
            # Setup mock
            mock_flock = MagicMock()
            mock_store = MagicMock()
            
            # Create expected result
            mock_result = EnhancedPrompt(
                enhanced_prompt="A majestic fluffy cat with golden eyes",
                original_prompt="A cat"
            )
            mock_store.get_by_type = AsyncMock(return_value=[mock_result])
            
            mock_flock.store = mock_store
            mock_flock.publish = AsyncMock()
            mock_flock.run_until_idle = AsyncMock()
            
            # Mock the agent builder chain
            mock_builder = MagicMock()
            mock_builder.description.return_value = mock_builder
            mock_builder.consumes.return_value = mock_builder
            mock_builder.publishes.return_value = mock_builder
            mock_flock.agent.return_value = mock_builder
            
            MockFlock.return_value = mock_flock
            
            # Run the function
            result = await run_flock_async(
                model="openai/gpt-4o",
                prompt="A cat",
                agent_instruction="Make it majestic"
            )
            
            # Verify result
            assert result == "A majestic fluffy cat with golden eyes"
            
            # Verify publish was called with correct artifact
            mock_flock.publish.assert_called_once()
            call_args = mock_flock.publish.call_args[0][0]
            assert isinstance(call_args, PromptEnhanceRequest)
            assert call_args.user_prompt == "A cat"
            assert call_args.user_instruction == "Make it majestic"
            
            # Verify run_until_idle was called
            mock_flock.run_until_idle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_flock_async_returns_none_on_no_result(self):
        """Test that run_flock_async returns None when no result is produced."""
        from pyros_cli.agents.flock_handler import run_flock_async
        
        with patch('pyros_cli.agents.flock_handler.Flock') as MockFlock:
            mock_flock = MagicMock()
            mock_store = MagicMock()
            mock_store.get_by_type = AsyncMock(return_value=[])  # No results
            
            mock_flock.store = mock_store
            mock_flock.publish = AsyncMock()
            mock_flock.run_until_idle = AsyncMock()
            
            mock_builder = MagicMock()
            mock_builder.description.return_value = mock_builder
            mock_builder.consumes.return_value = mock_builder
            mock_builder.publishes.return_value = mock_builder
            mock_flock.agent.return_value = mock_builder
            
            MockFlock.return_value = mock_flock
            
            result = await run_flock_async(
                model="openai/gpt-4o",
                prompt="Test prompt"
            )
            
            assert result is None
    
    def test_create_flock_sync_wrapper(self):
        """Test that create_flock provides sync wrapper."""
        from pyros_cli.agents.flock_handler import create_flock
        
        with patch('pyros_cli.agents.flock_handler.run_flock_async') as mock_async:
            mock_async.return_value = "Enhanced prompt result"
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Enhanced prompt result"
                
                result = create_flock(
                    model="openai/gpt-4o",
                    prompt="Test",
                    agent_instruction="Enhance"
                )
                
                mock_run.assert_called_once()


class TestEnhancePromptTool:
    """Tests for the enhance_prompt tool."""
    
    def test_enhance_prompt_tool_returns_enhanced_text(self):
        """Test that enhance_prompt tool returns enhanced prompt."""
        from pyros_cli.agents.tools import enhance_prompt
        
        with patch('pyros_cli.agents.tools.load_config') as mock_config:
            mock_config.return_value = MagicMock(model_name="openai/gpt-4o")
            
            with patch('pyros_cli.agents.tools.Flock') as MockFlock:
                mock_flock = MagicMock()
                mock_store = MagicMock()
                
                mock_result = EnhancedPrompt(
                    enhanced_prompt="Beautiful enhanced prompt"
                )
                mock_store.get_by_type = AsyncMock(return_value=[mock_result])
                
                mock_flock.store = mock_store
                mock_flock.publish = AsyncMock()
                mock_flock.run_until_idle = AsyncMock()
                
                mock_builder = MagicMock()
                mock_builder.description.return_value = mock_builder
                mock_builder.consumes.return_value = mock_builder
                mock_builder.publishes.return_value = mock_builder
                mock_flock.agent.return_value = mock_builder
                
                MockFlock.return_value = mock_flock
                
                result = enhance_prompt("Original prompt", "Make it better")
                
                assert result == "Beautiful enhanced prompt"
    
    def test_enhance_prompt_tool_returns_original_on_no_result(self):
        """Test fallback to original prompt when no enhancement produced."""
        from pyros_cli.agents.tools import enhance_prompt
        
        with patch('pyros_cli.agents.tools.load_config') as mock_config:
            mock_config.return_value = MagicMock(model_name="openai/gpt-4o")
            
            with patch('pyros_cli.agents.tools.Flock') as MockFlock:
                mock_flock = MagicMock()
                mock_store = MagicMock()
                mock_store.get_by_type = AsyncMock(return_value=[])  # No results
                
                mock_flock.store = mock_store
                mock_flock.publish = AsyncMock()
                mock_flock.run_until_idle = AsyncMock()
                
                mock_builder = MagicMock()
                mock_builder.description.return_value = mock_builder
                mock_builder.consumes.return_value = mock_builder
                mock_builder.publishes.return_value = mock_builder
                mock_flock.agent.return_value = mock_builder
                
                MockFlock.return_value = mock_flock
                
                result = enhance_prompt("Original prompt")
                
                # Should return original prompt as fallback
                assert result == "Original prompt"

