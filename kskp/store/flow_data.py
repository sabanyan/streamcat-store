from typing import Callable

class FlowData():
    """
    Flowデータを表す
    """
    def __init__(self,
                 flow_json:dict = {},
                 is_readable:Callable[[str],bool] = None,
                 readable_or_raise:Callable[[],None] = None, 
                 executable_or_raise:Callable[[],None] = None):
        self._flow_json = flow_json

        # readable_or_raise()が指定されない場合は権限判定をしない
        true_func = lambda uuid: True
        empty_func = lambda: None
        self._is_readable = is_readable or true_func
        self._readable_or_raise = readable_or_raise or empty_func
        self._executable_or_raise = executable_or_raise or empty_func

    def _mask_unreadble_nodes(self, nodes):
        if nodes is None:
            return
        for node in nodes:
            node_uuid = node.get('uuid')
            if node_uuid is None or node_uuid=='':
                continue
            if not self._is_readable(node_uuid):
                node['uuid'] = None
                node['label'] = '******'
                # ノードをマスクしたことを示すフラグを追加する
                node['hidden'] = True

    def _unmask_nodes(self, nodes, prev_ver_nodes):
        """
        prev_ver_nodesを参照してノードのマスクを外す
        """
        if nodes is None:
            return
        for node in nodes:
            if not node.get('hidden'):
                continue
            # 前の版のフローJsonから同じidのノードを取得する
            original_node = FlowData._find_node(prev_ver_nodes)
            # ノードをマスクしたことを示すフラグを削除する
            del node['hidden']
            if original_node is not None and not original_node.get('hidden'):
                # マスクを外す
                node['uuid'] = original_node.get('uuid')
                node['label'] = original_node.get('label')

    @staticmethod
    def _find_node(nodes, node_id):
        """
        指定したidのノードを取得する
        """
        if nodes is None or len(nodes)==0:
            return None
        
        for node in nodes:
            if node.get('id') == node_id:
                return node
        
        # 指定したidのノードがない場合はNoneを返す
        return None

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
        # 権限を判定する
        self._has_auth_or_raise(use_exec_auth)

        # 参照権限の無いサブフローやデータソースのラベルとuuidを秘匿する
        nodes = self._flow_json.get('nodes')
        self._mask_unreadble_nodes(nodes)

        return self._flow_json.get('nodes')

    def unmask_nodes(self, prev_flow_data):
        nodes = self._flow_json.get('nodes')
        prev_ver_nodes = prev_flow_data._flow_json.get('nodes')
        # マスクされたノードがあればマスクを外す
        self._unmask_nodes(nodes, prev_ver_nodes)

    def _has_auth_or_raise(self, use_exec_auth):
        if use_exec_auth:
            # フロー実行のための参照であれば、実行権限で判定する
            self._executable_or_raise()
        else:
            # 参照権限が無ければ例外を送出する
            self._readable_or_raise()

    def to_json(self, contains_nodes=True):
        if contains_nodes:
            # 参照権限が無ければ例外を送出する
            self._readable_or_raise()

            # 参照権限の無いサブフローやデータソースのラベルとuuidを秘匿する
            nodes = self._flow_json.get('nodes')
            self._mask_unreadble_nodes(nodes)

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

    def __eq__(self, other):
        return self._flow_json == other._flow_json

    def __ne__(self, other):
        return self._flow_json != other._flow_json
