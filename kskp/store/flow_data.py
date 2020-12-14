from typing import Callable

class FlowData():
    """
    Flowデータを表す
    """
    def __init__(self, flow_json:dict, 
                 readable_or_raise:Callable[[],None] = None, 
                 executable_or_raise:Callable[[],None] = None):
        self._flow_json = flow_json

        # readable_or_raise()が指定されない場合は権限判定をしない
        empty_func = lambda: None
        self._readable_or_raise = readable_or_raise or empty_func
        self._executable_or_raise = executable_or_raise or empty_func

    @property
    def label(self) -> str:
        return self._flow_json.get('label')

    @property
    def description(self) -> str:
        return self._flow_json.get('description')

    @property
    def creator(self) -> str:
        return self._flow_json.get('creator')

    @property
    def created_at(self) -> str:
        return self._flow_json.get('createdAt')

    @property
    def params(self) -> list:
        return self._flow_json.get('params')

    @property
    def ports(self) -> list:
        return self._flow_json.get('ports')

    @property
    def has_nodes(self):
        return 'nodes' in self._flow_json

    def get_nodes(self, use_exec_auth=False) -> list:
        if use_exec_auth:
            # フロー実行のための参照であれば、実行権限で判定する
            self._executable_or_raise()
        else:
            # 参照権限が無ければ例外を送出する
            self._readable_or_raise()

        return self._flow_json.get('nodes')

    def to_json(self, contains_nodes=True):

        if contains_nodes:
            # 参照権限が無ければ例外を送出する
            self._readable_or_raise()
            return self._flow_json
        else:
            return {
                'label': self.label,
                'description': self.description,
                'creator': self.creator,
                'createdAt': self.created_at,
                'params': self.params,
                'ports': self.ports
            }
