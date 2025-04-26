"""
Custom exceptions for the Pyros CLI application.

This module contains a hierarchy of custom exceptions that allow for more granular
error handling and more helpful error messages for users.
"""

class PyrosError(Exception):
    """Base exception class for all Pyros CLI errors."""
    def __init__(self, message="An error occurred in Pyros CLI", *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)
        
    def __str__(self):
        return self.message


class ConfigurationError(PyrosError):
    """Exception raised for errors in the configuration."""
    def __init__(self, message="Configuration error", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ConnectionError(PyrosError):
    """Exception raised for errors in connecting to external services."""
    def __init__(self, message="Connection error", service=None, *args, **kwargs):
        self.service = service
        if service:
            message = f"Connection error with {service}: {message}"
        super().__init__(message, *args, **kwargs)


class WorkflowError(PyrosError):
    """Exception raised for errors in workflow files or processing."""
    def __init__(self, message="Workflow error", workflow=None, *args, **kwargs):
        self.workflow = workflow
        if workflow:
            message = f"Workflow error in '{workflow}': {message}"
        super().__init__(message, *args, **kwargs)


class PromptError(PyrosError):
    """Exception raised for errors in prompt generation or processing."""
    def __init__(self, message="Prompt processing error", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class APIError(PyrosError):
    """Exception raised for errors in API communication."""
    def __init__(self, message="API error", api_name=None, status_code=None, *args, **kwargs):
        self.api_name = api_name
        self.status_code = status_code
        
        if api_name and status_code:
            message = f"{api_name} API error (status {status_code}): {message}"
        elif api_name:
            message = f"{api_name} API error: {message}"
        
        super().__init__(message, *args, **kwargs)


class ImageError(PyrosError):
    """Exception raised for errors in image processing or management."""
    def __init__(self, message="Image processing error", image_path=None, *args, **kwargs):
        self.image_path = image_path
        if image_path:
            message = f"Image error with '{image_path}': {message}"
        super().__init__(message, *args, **kwargs)


class AuthenticationError(PyrosError):
    """Exception raised for errors in authentication."""
    def __init__(self, message="Authentication error", service=None, *args, **kwargs):
        self.service = service
        if service:
            message = f"Authentication error with {service}: {message}"
        super().__init__(message, *args, **kwargs)


class ValidationError(PyrosError):
    """Exception raised for errors in data validation."""
    def __init__(self, message="Validation error", field=None, *args, **kwargs):
        self.field = field
        if field:
            message = f"Validation error in '{field}': {message}"
        super().__init__(message, *args, **kwargs)


class FileSystemError(PyrosError):
    """Exception raised for errors in file system operations."""
    def __init__(self, message="File system error", path=None, *args, **kwargs):
        self.path = path
        if path:
            message = f"File system error with path '{path}': {message}"
        super().__init__(message, *args, **kwargs) 