# Test Plan for Critical Fixes

This document outlines a comprehensive testing strategy for verifying the critical fixes implemented in the Pyros CLI.

## 1. Error Handling and Recovery Tests

### WebSocket Connection Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Normal Connection | Start ComfyUI and connect normally | Connection established successfully |
| Delayed Start | Try to connect before ComfyUI starts, then start ComfyUI | Connection retries and eventually succeeds |
| Connection Drop | Simulate network interruption during a session | Connection retries and recovers |
| Permanent Failure | Attempt to connect to non-existent ComfyUI server | Clear error message after max retry attempts |
| Timeout Handling | Simulate slow response from ComfyUI | Connection maintained with proper timeouts |

### Error Handling Framework Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Configuration Error | Provide invalid configuration data | ConfigurationError caught with helpful message |
| Connection Error | Run with ComfyUI server down | ConnectionError caught with troubleshooting steps |
| Workflow Error | Use invalid workflow file | WorkflowError caught with appropriate guidance |
| Prompt Error | Submit malformed prompt | PromptError caught with proper message |
| API Error | Simulate API failure (invalid response) | APIError caught with clear message |
| Image Error | Use invalid image directory | ImageError caught with helpful guidance |
| Unexpected Error | Force an unexpected exception | Graceful handling with detailed logs |

## 2. Security Improvements Tests

### Credential Storage Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Store API Key | Save a new API key | Key stored securely in system keyring |
| Retrieve API Key | Get previously stored API key | Key retrieved successfully |
| Update API Key | Update an existing API key | Key updated in system keyring |
| Delete API Key | Remove a stored API key | Key deleted from system keyring |
| Environment Override | Set API key in environment variable | Environment variable takes precedence |
| Invalid Credential | Attempt to use invalid credential | Proper error handling and user notification |

### Configuration Command Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| OpenAI Config | Configure OpenAI provider | API key stored securely, not in .env file |
| Anthropic Config | Configure Anthropic provider | API key stored securely, not in .env file |
| Groq Config | Configure Groq provider | API key stored securely, not in .env file |
| Gemini Config | Configure Gemini provider | API key stored securely, not in .env file |
| Ollama Config | Configure Ollama provider | Local configuration without API key |
| Reconfigure | Change provider after initial setup | Previous configuration properly overwritten |

## 3. Input Validation Tests

### Model Validation Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Valid UserMessages | Create with valid data | Instance created successfully |
| Empty Node ID | Create WorkflowProperty with empty node_id | Validation error raised |
| Empty Property | Create WorkflowProperty with empty property | Validation error raised |
| Long Message | Create HistoryItem with >10000 char message | Validation error raised |
| Control Characters | Create prompt with control characters | Characters removed in validation |
| Valid Conversion | Convert to/from JSON | Data preserved correctly |

### Path Safety Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Normal Path | Join paths within base directory | Path joined correctly |
| Directory Traversal | Attempt path with "../" to escape | None returned, path rejected |
| Absolute Path | Attempt to use absolute path | Properly handled relative to base |
| Symbolic Link | Use path with symbolic links | Properly resolved and validated |
| Long Path | Use extremely long path name | Properly handled without buffer issues |

### Input Sanitization Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Normal Prompt | Input standard prompt text | Processed normally |
| Control Characters | Input text with control chars | Characters removed |
| Very Long Prompt | Input >10000 character prompt | Truncated with warning |
| Malicious Input | Input potential command injection | Sanitized safely |
| Unicode Input | Input with various Unicode chars | Properly handled |

## Test Environment Setup

1. **Local Development Environment**:
   - Standard dev environment with all dependencies
   - Local ComfyUI installation for integration testing

2. **Simulated Production Environment**:
   - Clean installation on target OS
   - Fresh ComfyUI setup
   - No pre-existing configuration files

3. **Network Simulation Tools**:
   - Tools to simulate network latency and drops
   - Proxy for intercepting API requests

## Testing Schedule

1. **Unit Tests** (First Phase):
   - Development of automated tests for each component
   - Run with each code change

2. **Integration Tests** (Second Phase):
   - Tests that verify interaction between components
   - Run daily during active development

3. **System Tests** (Third Phase):
   - End-to-end workflows with real ComfyUI
   - Run before each release

## Reporting and Documentation

1. **Test Reports**:
   - Summary of tests run and results
   - Detailed logs of failures
   - Screenshots of user-facing errors

2. **Coverage Reports**:
   - Measurement of code coverage by tests
   - Identification of untested code paths

3. **Regression Detection**:
   - Comparison with previous test runs
   - Alert on new failures

## Automation Strategy

1. **CI/CD Integration**:
   - Automated unit and integration tests on push
   - Test status badges in repository

2. **Local Development Testing**:
   - Pre-commit hooks for basic validation
   - Easy-to-run test suite for developers

This test plan provides a comprehensive framework for verifying the critical fixes and ensuring they address the identified issues effectively. 