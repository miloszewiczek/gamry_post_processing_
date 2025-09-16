from experiments import Experiment
from typing import Any
from dataclasses import dataclass

@dataclass
class TreeNode:
    treeview_id: str
    text: str
    node_type: str
    experiments: Experiment | list[Experiment]
    other_info: Any