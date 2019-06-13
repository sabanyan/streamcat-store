import os
from pathlib import Path

from . import PathFileSource

class CommandsPathFileSource(PathFileSource):
    """
    コマンドJSONの一覧が入ったパスを持つsource
    """

    def __init__(self, visible_command):
        path = Path(__file__).resolve()
        commands_path = path.parent.joinpath('commands') / visible_command / 'json'
        if commands_path.exists():
            super().__init__(commands_path)
