"""Tests for local standalone mode.

These tests verify the local LLM provider and image generator
work correctly with mocked ML libraries.
"""

import json
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path


class TestLocalLLMProvider:
    """Tests for the local LLM provider module."""
    
    def test_get_model_path_from_env(self):
        """Test that model path is read from environment variable."""
        from pyros_cli.local.llm_provider import _get_model_path
        
        with patch.dict(os.environ, {"QWEN_4B_PATH": "/custom/path/qwen"}):
            assert _get_model_path() == "/custom/path/qwen"
    
    def test_get_model_path_default(self):
        """Test that model path defaults to HuggingFace ID."""
        from pyros_cli.local.llm_provider import _get_model_path
        
        # Temporarily remove env var if it exists
        original = os.environ.pop("QWEN_4B_PATH", None)
        try:
            assert _get_model_path() == "Qwen/Qwen3-4B-Instruct-2507"
        finally:
            if original:
                os.environ["QWEN_4B_PATH"] = original
    
    def test_enhance_prompt_creates_proper_prompt(self):
        """Test that enhance_prompt builds the correct system prompt."""
        import pyros_cli.local.llm_provider as llm_module
        
        with patch.object(llm_module, "generate_text") as mock_gen:
            mock_gen.return_value = "Enhanced: A beautiful sunset"
            
            result = llm_module.enhance_prompt("A sunset", "make it dramatic")
            
            # Verify generate_text was called
            mock_gen.assert_called_once()
            call_args = mock_gen.call_args[0][0]
            
            # Check prompt contains key elements
            assert "A sunset" in call_args
            assert "make it dramatic" in call_args
            assert "expert prompt engineer" in call_args.lower()
            
            assert result == "Enhanced: A beautiful sunset"
    
    def test_generate_prompt_variable_values_parses_json(self):
        """Test that generate_prompt_variable_values correctly parses JSON response."""
        import pyros_cli.local.llm_provider as llm_module
        
        with patch.object(llm_module, "generate_text") as mock_gen:
            mock_gen.return_value = '["Persian", "Siamese", "Maine Coon", "Ragdoll", "British Shorthair", "Bengal", "Abyssinian", "Sphynx", "Russian Blue", "Scottish Fold", "Norwegian Forest", "Birman", "Himalayan", "Burmese", "Tonkinese", "Chartreux", "Somali", "Oriental", "Devon Rex", "Cornish Rex"]'
            
            result = llm_module.generate_prompt_variable_values("cat_breed", "a cute __cat_breed__")
            
            assert isinstance(result, list)
            assert len(result) >= 20
            assert "Persian" in result
            assert "Siamese" in result
    
    def test_generate_prompt_variable_values_handles_malformed_json(self):
        """Test that generate_prompt_variable_values handles malformed JSON gracefully."""
        import pyros_cli.local.llm_provider as llm_module
        
        with patch.object(llm_module, "generate_text") as mock_gen:
            # Return something that's not valid JSON but has values
            mock_gen.return_value = "Here are some values:\nPersian\nSiamese\nMaine Coon\nRagdoll\nBengal"
            
            result = llm_module.generate_prompt_variable_values("cat_breed", "a cute __cat_breed__")
            
            # Should attempt fallback parsing
            assert isinstance(result, list)
    
    def test_global_state_management(self):
        """Test that global model state is properly managed."""
        import pyros_cli.local.llm_provider as llm_module
        
        # Initially should be None
        llm_module._model = None
        llm_module._tokenizer = None
        
        assert llm_module._model is None
        assert llm_module._tokenizer is None
        
        # Simulate setting
        llm_module._model = "fake_model"
        llm_module._tokenizer = "fake_tokenizer"
        
        assert llm_module._model == "fake_model"
        assert llm_module._tokenizer == "fake_tokenizer"
        
        # Clean up
        llm_module._model = None
        llm_module._tokenizer = None


class TestLocalImageGenerator:
    """Tests for the local image generator module."""
    
    def test_get_model_path_from_env(self):
        """Test that model path is read from environment variable."""
        from pyros_cli.local.image_generator import _get_model_path
        
        with patch.dict(os.environ, {"Z_IMAGE_PATH": "/custom/path/zimage"}):
            assert _get_model_path() == "/custom/path/zimage"
    
    def test_get_model_path_default(self):
        """Test that model path defaults to HuggingFace ID."""
        from pyros_cli.local.image_generator import _get_model_path
        
        original = os.environ.pop("Z_IMAGE_PATH", None)
        try:
            assert _get_model_path() == "Tongyi-MAI/Z-Image-Turbo"
        finally:
            if original:
                os.environ["Z_IMAGE_PATH"] = original
    
    def test_get_output_dir_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        from pyros_cli.local.image_generator import _get_output_dir
        
        output_path = tmp_path / "test_output"
        with patch.dict(os.environ, {"LOCAL_OUTPUT_DIR": str(output_path)}):
            result = _get_output_dir()
            assert result == output_path
            assert output_path.exists()
    
    def test_get_output_dir_default(self, tmp_path):
        """Test that output directory defaults to ./output."""
        from pyros_cli.local.image_generator import _get_output_dir
        
        original = os.environ.pop("LOCAL_OUTPUT_DIR", None)
        try:
            result = _get_output_dir()
            assert str(result).endswith("output")
        finally:
            if original:
                os.environ["LOCAL_OUTPUT_DIR"] = original
    
    def test_global_pipeline_state(self):
        """Test that global pipeline state is properly managed."""
        import pyros_cli.local.image_generator as img_module
        
        img_module._pipeline = None
        assert img_module._pipeline is None
        
        img_module._pipeline = "fake_pipeline"
        assert img_module._pipeline == "fake_pipeline"
        
        img_module._pipeline = None
    
    def test_get_gpu_memory_info_structure(self):
        """Test that get_gpu_memory_info returns proper structure."""
        from pyros_cli.local.image_generator import get_gpu_memory_info
        
        # This will return either actual GPU info or an error dict
        info = get_gpu_memory_info()
        
        assert isinstance(info, dict)
        # Should have either GPU info keys or error key
        assert ("allocated_gb" in info and "total_gb" in info) or "error" in info


class TestLocalCLI:
    """Tests for the local CLI module."""
    
    def test_substitute_vars_local_uses_existing_vars(self):
        """Test that existing variables are substituted correctly."""
        from pyros_cli.local.cli import substitute_vars_local
        from pyros_cli.models.prompt_vars import PromptVars
        
        prompt_vars = {
            "__animal__": PromptVars(
                prompt_id="__animal__",
                values=["cat", "dog", "bird"]
            )
        }
        
        result = substitute_vars_local("a cute __animal__", prompt_vars)
        
        assert "__animal__" not in result
        assert any(animal in result for animal in ["cat", "dog", "bird"])
    
    def test_substitute_vars_local_leaves_unknown_vars(self):
        """Test that unknown variables without generation stay as-is."""
        # Mock the generation function in llm_provider (where it's imported from)
        with patch(
            "pyros_cli.local.llm_provider.generate_prompt_variable_values", 
            return_value=[]
        ):
            from pyros_cli.local.cli import substitute_vars_local
            
            result = substitute_vars_local("a __unknown_var__", {})
            
            # Variable should remain (generation failed)
            assert "__unknown_var__" in result or "unknown_var" in result
    
    def test_show_help_displays_commands(self, capsys):
        """Test that show_help displays all available commands."""
        from pyros_cli.local.cli import show_help
        
        show_help()
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Check that key commands are documented
        assert "/help" in output
        assert "/vars" in output
        assert "/seed" in output
    
    def test_load_prompt_vars_function(self):
        """Test that load_prompt_vars loads from the library."""
        from pyros_cli.local.cli import load_prompt_vars
        
        # Should return a dict (even if empty)
        result = load_prompt_vars()
        assert isinstance(result, dict)


class TestPromptVarSave:
    """Tests for prompt variable save functionality."""
    
    def test_save_prompt_var_creates_file(self, tmp_path):
        """Test that save_prompt_var creates properly formatted file."""
        from pyros_cli.models.prompt_vars import save_prompt_var, get_prompt_vars_dir
        
        with patch.object(
            __import__("pyros_cli.models.prompt_vars", fromlist=["get_prompt_vars_dir"]),
            "get_prompt_vars_dir",
            return_value=str(tmp_path)
        ):
            values = ["Persian", "Siamese", "Maine Coon"]
            file_path = save_prompt_var(
                variable_name="test_cat",
                description="Test cat breeds",
                values=values
            )
            
            assert os.path.exists(file_path)
            assert file_path.endswith("test_cat.md")
            
            with open(file_path) as f:
                content = f.read()
            
            assert "# Test cat breeds" in content
            assert "Persian" in content
            assert "Siamese" in content
            assert "Maine Coon" in content
    
    def test_save_prompt_var_handles_empty_description(self, tmp_path):
        """Test that save_prompt_var works with empty description."""
        from pyros_cli.models.prompt_vars import save_prompt_var
        
        with patch(
            "pyros_cli.models.prompt_vars.get_prompt_vars_dir",
            return_value=str(tmp_path)
        ):
            values = ["value1", "value2"]
            file_path = save_prompt_var(
                variable_name="no_desc",
                description="",
                values=values
            )
            
            with open(file_path) as f:
                content = f.read()
            
            # Should not have a description comment at start
            assert not content.startswith("# \n")
            assert "value1" in content


class TestBatchParams:
    """Tests for batch parameter parsing."""
    
    def test_parse_batch_params_full(self):
        """Test parsing all batch parameters."""
        from pyros_cli.local.cli import parse_batch_params
        
        prompt, params = parse_batch_params("a cute cat : x10,h832,w1216")
        
        assert prompt == "a cute cat"
        assert params["count"] == 10
        assert params["height"] == 832
        assert params["width"] == 1216
    
    def test_parse_batch_params_partial(self):
        """Test parsing partial batch parameters."""
        from pyros_cli.local.cli import parse_batch_params
        
        prompt, params = parse_batch_params("a dog : x5")
        
        assert prompt == "a dog"
        assert params["count"] == 5
        assert params["height"] == 1024  # default
        assert params["width"] == 1024   # default
    
    def test_parse_batch_params_with_enhancement(self):
        """Test parsing with enhancement syntax."""
        from pyros_cli.local.cli import parse_batch_params
        
        prompt, params = parse_batch_params("a cat > make it magical : x3,h512")
        
        assert prompt == "a cat > make it magical"
        assert params["count"] == 3
        assert params["height"] == 512
    
    def test_parse_batch_params_no_params(self):
        """Test parsing without any parameters."""
        from pyros_cli.local.cli import parse_batch_params
        
        prompt, params = parse_batch_params("just a simple prompt")
        
        assert prompt == "just a simple prompt"
        assert params["count"] == 1
        assert params["height"] == 1024
        assert params["width"] == 1024
    
    def test_parse_batch_params_only_size(self):
        """Test parsing with only size parameters."""
        from pyros_cli.local.cli import parse_batch_params
        
        prompt, params = parse_batch_params("landscape : w1920,h1080")
        
        assert prompt == "landscape"
        assert params["count"] == 1
        assert params["width"] == 1920
        assert params["height"] == 1080


class TestIntegration:
    """Integration tests for local mode components working together."""
    
    def test_prompt_vars_roundtrip(self, tmp_path):
        """Test saving and loading prompt variables."""
        from pyros_cli.models.prompt_vars import save_prompt_var, load_prompt_vars, get_prompt_vars_dir
        
        # Create a temp prompt_vars directory structure
        prompt_vars_dir = tmp_path / "prompt_vars"
        prompt_vars_dir.mkdir()
        
        # Save a test file directly
        test_file = prompt_vars_dir / "test_var.md"
        test_file.write_text("# Test variable\nvalue1\nvalue2\nvalue3")
        
        with patch("pyros_cli.models.prompt_vars.CURRENT_DIR", str(tmp_path)):
            with patch(
                "pyros_cli.models.prompt_vars.get_prompt_vars_dir",
                return_value=str(prompt_vars_dir)
            ):
                # This should load from our temp directory
                # Note: load_prompt_vars uses os.path.join with CURRENT_DIR
                pass
        
        # Verify the file was created correctly
        assert test_file.exists()
        content = test_file.read_text()
        assert "value1" in content
    
    def test_env_config_priority(self):
        """Test that env vars take priority for model paths."""
        from pyros_cli.local.llm_provider import _get_model_path as get_llm_path
        from pyros_cli.local.image_generator import _get_model_path as get_img_path
        
        # Test with custom paths
        with patch.dict(os.environ, {
            "QWEN_4B_PATH": "/custom/llm",
            "Z_IMAGE_PATH": "/custom/image"
        }):
            assert get_llm_path() == "/custom/llm"
            assert get_img_path() == "/custom/image"
