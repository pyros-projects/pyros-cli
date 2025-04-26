# Workflow Integration

## Overview
Pyros CLI integrates with ComfyUI workflows by dynamically modifying specified nodes in the workflow JSON before sending it to the ComfyUI API. This allows users to maintain complex workflows while changing only the necessary parameters through the CLI.

## Workflow File Format
- ComfyUI workflows are stored as JSON files
- Each node has a unique identifier
- Nodes contain input/output connections and parameters
- Workflow files can be exported directly from ComfyUI in API mode

## Required Workflow Components
For Pyros CLI to work correctly, the workflow must include:

1. **Prompt Node**:
   - A text node where the prompt will be inserted
   - Must have a configurable text property

2. **Steps Node**:
   - Controls the number of sampling steps
   - Used for generation quality control

3. **Seed Node**:
   - Controls the random seed for generation
   - Ensures reproducibility of results

## Workflow Implementation
The workflow is managed using:
- Pydantic models for validation (`ComfyUIWorkflow`)
- JSON processing for loading and updating
- Logger for tracking workflow modifications

## Workflow Configuration
During setup, the user must specify:

1. The path to the workflow JSON file
2. The node ID for the prompt node
3. The property name within the prompt node (usually "text" or "prompt")
4. The node ID for the steps node
5. The property name within the steps node
6. The node ID for the seed node
7. The property name within the seed node

These configurations are stored in environment variables and reused in subsequent sessions.

## Workflow Loading Process
Workflow loading is handled by the `load_workflow()` function:
```python
def load_workflow(filepath: str) -> ComfyUIWorkflow:
    """Loads workflow from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            raw_json = json.load(f)
        workflow = ComfyUIWorkflow.model_validate(raw_json)
        return workflow
    except FileNotFoundError:
        # Handle file not found
    except json.JSONDecodeError:
        # Handle invalid JSON
    except ValidationError:
        # Handle validation error
```

1. The workflow file is read from disk
2. The JSON is parsed and validated against the ComfyUIWorkflow model
3. Basic validation ensures all required nodes exist
4. The workflow is returned as a validated model

## Workflow Modification
When a prompt is submitted, `update_workflow()` is called to prepare the workflow:

```python
def update_workflow(
    workflow: ComfyUIWorkflow,
    prompt_text: str,
    seed: int,
    settings: ComfyUISettings,
    user_messages: UserMessages
) -> Dict[str, Any]:
    """Updates the workflow dictionary with new prompt and seed."""
    workflow_dict = workflow.model_dump(mode='python')
    
    # Update Prompt
    if settings.prompt_node_id in workflow_dict:
        workflow_dict[settings.prompt_node_id]['inputs'][settings.prompt_node_property] = prompt_text
        
    # Update Seed
    if settings.denoise_node_id in workflow_dict:
        workflow_dict[settings.denoise_node_id]['inputs'][settings.denoise_node_property] = seed
        
    # Update additional workflow properties
    if user_messages.workflow_properties:
        for property in user_messages.workflow_properties:
            if property.node_id in workflow_dict:
                workflow_dict[property.node_id]['inputs'][property.node_property] = property.value
                
    return workflow_dict
```

1. A deep copy of the base workflow is created
2. The prompt text is inserted into the specified prompt node/property
3. The random seed is set for reproducibility
4. Any additional workflow properties from commands are applied
5. The modified workflow is returned as a dictionary for API submission

## Dynamic Workflow Properties
Commands can modify additional workflow properties through the `WorkflowProperty` class:

```python
class WorkflowProperty:
    node_id: str
    node_property: str
    value: Any
```

- Workflow properties are defined by:
  - Node ID (which node to modify)
  - Node property (which property within the node)
  - Value (what value to set)

- Examples:
  - Changing sampler type
  - Adjusting CFG scale
  - Setting image dimensions

## Workflow Export
- Generated workflow JSONs can be exported for later use
- This allows saving successful configurations

## Workflow Compatibility
- Pyros CLI is designed to work with most standard ComfyUI workflows
- Custom nodes can be supported as long as they follow the standard property structure
- Complex workflows with multiple text inputs may require more configuration

## Error Handling
- Missing nodes or properties are logged with warnings
- Invalid JSON workflow files are detected with clear error messages
- Runtime errors during workflow modification are captured with detailed logging
- File not found errors include path information 