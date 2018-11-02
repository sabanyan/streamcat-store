import os
from pathlib import Path

from . import PathFileSource

class CommandsPathFileSource(PathFileSource):
    """
    コマンドJSONの一覧が入ったパスを持つsource
    """

    def __init__(self):    
        path = Path(__file__).resolve()
        commands_path = path.parent.parent.parent.joinpath('commands')        
        super().__init__(commands_path)
