from experiments import Experiment
from typing import Any
from dataclasses import dataclass

@dataclass
class TreeNode:
    treeview_id: str
    text: str
    node_type: str
    experiments: Experiment | list[Experiment]
    values: Any
    other_info: Any = None
    image: Any = None



