from datetime import datetime
import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


class WorkflowProperty(BaseModel):
    node_id: str
    node_property: str
    value: str
    alias: str

class HistoryItem(BaseModel):
    type: Literal["base_prompt", "evaluated_prompt", "command"]
    message: str
    timestamp: str

class UserMessages(BaseModel):
    base_prompt: str	
    evaluated_prompt: str
    command: str
    history: list[HistoryItem]
    session_history: list[HistoryItem] = Field(default_factory=list, exclude=True)
    workflow_properties: list[WorkflowProperty]

    def __init__(self, base_prompt: str, evaluated_prompt: str, command: str, history: list[HistoryItem], workflow_properties: list[WorkflowProperty]):
        super().__init__(base_prompt=base_prompt, evaluated_prompt=evaluated_prompt, command=command, history=history, workflow_properties=workflow_properties)

    def add_message(self, message: str, type: Literal["base_prompt", "evaluated_prompt", "command"]):
        self.history.append(HistoryItem(message=message, type=type, timestamp=datetime.now().isoformat()))
        self.session_history.append(HistoryItem(message=message, type=type, timestamp=datetime.now().isoformat()))
        self.save_to_file()

    def set_command(self, command: str):
        self.command = command
        self.history.append(HistoryItem(message=command, type="command", timestamp=datetime.now().isoformat()))
        self.session_history.append(HistoryItem(message=command, type="command", timestamp=datetime.now().isoformat()))
        self.save_to_file()
    
    def set_evaluated_prompt(self, evaluated_prompt: str):
        self.evaluated_prompt = evaluated_prompt
        self.history.append(HistoryItem(message=evaluated_prompt, type="evaluated_prompt", timestamp=datetime.now().isoformat()))
        self.session_history.append(HistoryItem(message=evaluated_prompt, type="evaluated_prompt", timestamp=datetime.now().isoformat()))
        self.save_to_file()


    def set_base_prompt(self, base_prompt: str):
        self.base_prompt = base_prompt
        self.history.append(HistoryItem(message=base_prompt, type="base_prompt", timestamp=datetime.now().isoformat()))
        self.session_history.append(HistoryItem(message=base_prompt, type="base_prompt", timestamp=datetime.now().isoformat()))
        self.save_to_file()

    def set_workflow_properties(self, workflow_properties: list[WorkflowProperty]):
        self.workflow_properties = workflow_properties
        self.save_to_file()

    def add_workflow_property(self, workflow_property: WorkflowProperty):
        self.workflow_properties.append(workflow_property)
        self.save_to_file()

    def get_workflow_properties(self):
        return self.workflow_properties
    
    def get_workflow_property(self, node_id: str, node_property: str):
        for workflow_property in self.workflow_properties:
            if workflow_property.node_id == node_id and workflow_property.node_property == node_property:
                return workflow_property
        return None

    def get_base_prompt(self):
        return self.base_prompt

    def get_history(self):
        return self.history

    def get_evaluated_prompt(self):
        return self.evaluated_prompt
    
    def to_json(self):
        return self.model_dump_json()
    
    def to_dict(self):
        return self.model_dump()
    
    def from_json(self, json_str: str):
        return self.model_validate_json(json_str)
    
    def from_dict(self, data: dict):
        return self.model_validate(data)
    

    def save_to_file(self, file_path: str|Path|None=None):
        if file_path is None:
            file_path = "user_messages.json"
        with open(file_path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, file_path: str|Path|None=None):
        if file_path is None:
            file_path = "user_messages.json"

        if not os.path.exists(file_path):
            return cls(base_prompt="", evaluated_prompt="", command="", history=[], workflow_properties=[])

        with open(file_path, "r") as f:
            json_str = f.read()
            return cls.from_json(cls,json_str)
    
    
    
    
