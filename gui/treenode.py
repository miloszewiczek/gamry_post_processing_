from experiments import Experiment
from typing import Any
from dataclasses import dataclass

@dataclass
class TreeNode:
    treeview_id: str
    text: str
    node_type: str
    experiments: Experiment | list[Experiment]
    values: dict
    other_info: dict = None
    image: Any = None


    @property
    def main_info(self) -> tuple[str, str, dict]:
        return {'treeview_id': self.treeview_id,
                'text': self.text,
                #this unpacks the values into each category
                **self.values}
    