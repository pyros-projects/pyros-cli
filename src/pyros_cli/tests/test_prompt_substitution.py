import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from pyros_cli.services.prompt_substitution import substitute_prompt_vars
from pyros_cli.models.prompt_vars import PromptVars

class TestPromptSubstitution(unittest.TestCase):
    @patch('pyros_cli.services.prompt_substitution.load_prompt_vars')
    @patch('pyros_cli.services.prompt_substitution.console')
    def test_basic_variable_substitution(self, mock_console, mock_load_vars):
        # Mock the prompt_vars dictionary
        test_vars = {
            "__test__": PromptVars(
                prompt_id="__test__",
                file_path="test.txt",
                description="Test variable",
                values=["value1", "value2", "value3"]
            )
        }
        mock_load_vars.return_value = test_vars
        
        # Test with a fixed seed for deterministic random choice
        with patch('random.choice', return_value="value1"):
            result = substitute_prompt_vars("This is a __test__ prompt")
            self.assertEqual(result, "This is a value1 prompt")
    
    @patch('pyros_cli.services.prompt_substitution.load_prompt_vars')
    @patch('pyros_cli.services.prompt_substitution.console')
    def test_indexed_variable_substitution(self, mock_console, mock_load_vars):
        # Mock the prompt_vars dictionary
        test_vars = {
            "__test__": PromptVars(
                prompt_id="__test__",
                file_path="test.txt",
                description="Test variable",
                values=["value1", "value2", "value3"]
            )
        }
        mock_load_vars.return_value = test_vars
        
        # Test using specific indices
        result = substitute_prompt_vars("First: __test:0__ Second: __test:1__ Third: __test:2__")
        self.assertEqual(result, "First: value1 Second: value2 Third: value3")
    
    @patch('pyros_cli.services.prompt_substitution.load_prompt_vars')
    @patch('pyros_cli.services.prompt_substitution.console')
    def test_invalid_index(self, mock_console, mock_load_vars):
        # Mock the prompt_vars dictionary
        test_vars = {
            "__test__": PromptVars(
                prompt_id="__test__",
                file_path="test.txt",
                description="Test variable",
                values=["value1", "value2", "value3"]
            )
        }
        mock_load_vars.return_value = test_vars
        
        # Test with an out-of-range index
        result = substitute_prompt_vars("This should remain unchanged: __test:999__")
        self.assertEqual(result, "This should remain unchanged: __test:999__")
    
    @patch('pyros_cli.services.prompt_substitution.load_prompt_vars')
    @patch('pyros_cli.services.prompt_substitution.console')
    def test_mixed_variables(self, mock_console, mock_load_vars):
        # Mock the prompt_vars dictionary
        test_vars = {
            "__test__": PromptVars(
                prompt_id="__test__",
                file_path="test.txt",
                description="Test variable",
                values=["value1", "value2", "value3"]
            )
        }
        mock_load_vars.return_value = test_vars
        
        # Test with a mix of indexed and random variables
        with patch('random.choice', return_value="value1"):
            result = substitute_prompt_vars("Random: __test__ Indexed: __test:2__")
            self.assertEqual(result, "Random: value1 Indexed: value3")

if __name__ == "__main__":
    unittest.main() 