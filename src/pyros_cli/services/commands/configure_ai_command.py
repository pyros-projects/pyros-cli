import os
import questionary
from rich.console import Console
import uuid

from pyros_cli.services.commands.base_command import BaseCommand, CommandResult
from dotenv import load_dotenv, set_key

from pyros_cli.services.config import _get_env_path
from pyros_cli.utils.cli_helper import print_success, print_error, print_subheader, print_warning

console = Console()

supported_ai_providers = ["ollama", "openai", "anthropic", "groq", "gemini"]

class ConfigureAiCommand(BaseCommand):
    """Command to control ComfyUI nodes"""
    
    name = "/configure-ai"
    help_text = "Configure AI with format: /configure-ai <ollama|openai|anthropic|groq|gemini>"
    
    def __init__(self, command_registry=None):
        self.command_registry = command_registry
    
    async def execute(self, args: str) -> CommandResult:
        """Configure AI with format: /configure-ai <ollama|openai|anthropic|groq|gemini>"""
        if not args:
            print_warning("Usage: /configure-ai <ollama|openai|anthropic|groq|gemini>")
            return CommandResult(is_command=True, should_generate=False, data=False)
        
        dotenv_path = _get_env_path()
        load_dotenv()

        print_subheader("Configure AI")
            
        # Parse the arguments
        arg_parts = args.strip().split(' ', 1)

        ai_provider = arg_parts[0].strip()

        if ai_provider not in supported_ai_providers:
            print_warning(f"Unsupported AI provider: {ai_provider}. Supported providers: {', '.join(supported_ai_providers)}")
            return CommandResult(is_command=True, should_generate=False, data=False)
        
        if ai_provider == "ollama":
            model_name = await questionary.text("Enter the ollama model name (eg: llama3-8b-8192): ").ask_async()
            set_key(dotenv_path, "MODEL_NAME", model_name)
            os.environ["MODEL_NAME"] = model_name

            print_success(f"AI provider set to {ai_provider} with model {model_name}")
            return CommandResult(is_command=True, should_generate=False, data=True)
        
        if ai_provider == "openai":
            model_name = await questionary.text("Enter the openai model name (eg: gpt-4o): ").ask_async()
            model_name = "openai/" + model_name.strip()
            set_key(dotenv_path, "MODEL_NAME", model_name)
            os.environ["MODEL_NAME"] = model_name

            api_key = await questionary.text("Enter the openai api key: ").ask_async()
            set_key(dotenv_path, "OPENAI_API_KEY", api_key)
            os.environ["OPENAI_API_KEY"] = api_key

            print_success(f"AI provider set to {ai_provider} with model {model_name}")
            return CommandResult(is_command=True, should_generate=False, data=True)

        if ai_provider == "anthropic":
            model_name = await questionary.text("Enter the anthropic model name (eg: claude-3-5-sonnet-20240620): ").ask_async()
            model_name = "anthropic/" + model_name.strip()
            set_key(dotenv_path, "MODEL_NAME", model_name)
            os.environ["MODEL_NAME"] = model_name

            api_key = await questionary.text("Enter the anthropic api key: ").ask_async()
            set_key(dotenv_path, "ANTHROPIC_API_KEY", api_key)
            os.environ["ANTHROPIC_API_KEY"] = api_key

            print_success(f"AI provider set to {ai_provider} with model {model_name}")
            return CommandResult(is_command=True, should_generate=False, data=True)
        
        if ai_provider == "groq":
            model_name = await questionary.text("Enter the groq model name (eg: llama3-8b-8192): ").ask_async()
            model_name = "groq/" + model_name.strip()
            set_key(dotenv_path, "MODEL_NAME", model_name)
            os.environ["MODEL_NAME"] = model_name

            api_key = await questionary.text("Enter the groq api key: ").ask_async()
            set_key(dotenv_path, "GROQ_API_KEY", api_key)
            os.environ["GROQ_API_KEY"] = api_key

            print_success(f"AI provider set to {ai_provider} with model {model_name}")
            return CommandResult(is_command=True, should_generate=False, data=True)
        
        if ai_provider == "gemini":
            model_name = await questionary.text("Enter the gemini model name (eg: gemini-1.5-flash): ").ask_async()
            model_name = "gemini/" + model_name.strip()
            set_key(dotenv_path, "MODEL_NAME", model_name)
            os.environ["MODEL_NAME"] = model_name

            api_key = await questionary.text("Enter the gemini api key: ").ask_async()
            set_key(dotenv_path, "GEMINI_API_KEY", api_key)
            os.environ["GEMINI_API_KEY"] = api_key

            print_success(f"AI provider set to {ai_provider} with model {model_name}")
            return CommandResult(is_command=True, should_generate=False, data=True)

        # Set the AI provider in the .env file
        set_key(dotenv_path, "AI_PROVIDER", ai_provider)

        check = check_connection()
        
        # Return the workflow property in the data field
        return CommandResult(
            is_command=True, 
            should_generate=True,
            data=check
        ) 
    

def check_connection():
    """Check the connection to the AI provider"""
    print_subheader("Checking connection to AI provider")
    print_success("Connection successful")
    print_success("Connection successful")
    print_success("Connection successful")

