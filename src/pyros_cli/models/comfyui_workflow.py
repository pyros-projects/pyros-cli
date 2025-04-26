from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from pydantic import RootModel


class MetaData(BaseModel):
    title: Optional[str] = None
    _prompt_id: Optional[str] = None


class NodeInput(RootModel[Union[Any, List[Union[str, int]]]]):
    pass


class Node(BaseModel):
    inputs: Dict[str, Union[NodeInput, Any]]
    class_type: str
    _meta: Optional[MetaData] = None


class ComfyUIWorkflow(RootModel[Dict[str, Node]]):
    pass