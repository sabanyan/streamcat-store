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

    @property
    def label(self) -> str:
        return self._flow_json.get('label')

    @label.setter
    def label(self, label):
        self._flow_json['label'] = label

    @property
    def description(self) -> str:
        return self._flow_json.get('description')

    @property
    def creator(self) -> str:
        return self._flow_json.get('creator')

    @creator.setter
    def creator(self, creator):
        self._flow_json['creator'] = creator

    @property
    def created_at(self) -> str:
        return self._flow_json.get('createdAt')

    @created_at.setter
    def created_at(self, created_at):
        self._flow_json['createdAt'] = created_at

    @property
    def params(self) -> list:
        return self._flow_json.get('params')

    @property
    def ports(self) -> list:
        return self._flow_json.get('ports')

    @property
    def has_nodes(self):
        return 'nodes' in self._flow_json

    def get_src_frame_uuids(self):
        """
        参照する入力frameを全て取得する
        """
        ret = []

        if not self.has_nodes:
            return ret

        for node in self.get_nodes():
            if node['type'] != 'frame':
                continue
            if 'cacheCreatedAt' in node and\
                node['cacheCreatedAt'] is not None and\
                node['cacheCreatedAt'] != '':
                # cacheCreatedAtに日時が入っている場合はキャッシュである
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def get_cache_frame_uuids(self):
        """
        参照するキャッシュframeを全て取得する
        """
        ret = []
        
        if not self.has_nodes:
            return ret

        for node in self.get_nodes():
            if node['type'] != 'frame':
                continue
            if 'cacheCreatedAt' not in node or\
                node['cacheCreatedAt'] is None or\
                node['cacheCreatedAt'] == '':
                # cacheCreatedAtに日時が入っていない場合は入力フレームである
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def get_sub_flow_uuids(self):
        """
        参照するSub Flowを全て取得する
        """
        ret = []

        if not self.has_nodes:
            return ret

        for node in self.get_nodes():
            if node['type'] != 'flow':
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def get_store_uuids(self):
        """
        参照するStoreを全て取得する
        """
        ret = []

        if not self.has_nodes:
            return ret

        for node in self.get_nodes():
            if node['type'] != 'store':
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def copy(self):
        """
        自身の複製を作成して返す
        """
        import copy
        return FlowData(copy.deepcopy(self._flow_json))

    def get_nodes(self, use_exec_auth=False) -> list:
        flow_json = self._authorize(self._flow_json, use_exec_auth)
        return flow_json.get('nodes')

    def unmask_nodes(self, prev_flow_json):
        """
        マスキングされる前のフローJson(prev_ver_nodes)を用いて、マスキングを解除する
        """
        nodes = self._flow_json.get('nodes')
        prev_ver_nodes = prev_flow_json.get('nodes')

        if nodes is None or prev_ver_nodes is None:
            return
        for node in nodes:
            if not node.get('masked'):
                continue

            # 前の版のフローJsonから同じidのノードを取得する
            original_node = FlowData._find_node(prev_ver_nodes, node['id'])

            if original_node is not None and not original_node.get('masked'):
                # マスクを外す
                node['uuid'] = original_node.get('uuid')
                node['label'] = original_node.get('label')

            # ノードをマスクしたことを示すフラグを削除する
            del node['masked']

    def to_json(self, contains_nodes=True):
        if contains_nodes:
            flow_json = self._authorize(self._flow_json)
            return flow_json
        else:
            return {
                'label': self.label,
                'description': self.description,
                'creator': self.creator,
                'createdAt': self.created_at,
                'params': self.params,
                'ports': self.ports
            }

    def _set_cache(self, node_id, cache_uuid):
        """
        指定するノードidにキャッシュを設定する
        """
        from datetime import datetime, timedelta, timezone

        if 'nodes' not in self._flow_json:
            return

        for node in self._flow_json.get('nodes'):
            if node['id'] == node_id:
                node['uuid'] = cache_uuid
                # TODO: 記録時間はUTC、表示時間は現地時間にすべきでは？？
                node['cacheCreatedAt'] = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y-%m-%d %H:%M:%S')
                # ノードidは重複しないので1つ設定したら処理を終了する
                break

    def _replace_uuid(self, old_uuid, new_uuid):
        """
        指定するuuidを置き換える
        """
        if 'nodes' not in self._flow_json:
            return
        for node in self._flow_json.get('nodes'):
            if 'uuid' not in node:
                continue
            if node['uuid'] == old_uuid:
                node['uuid'] = new_uuid

    def _authorize(self, flow_json, use_exec_auth=False):
        """
        権限の判定と、参照権限のないノードのマスキングをする
        """
        def has_auth_or_raise(flow_data, use_exec_auth):
            if use_exec_auth:
                # フロー実行のための参照であれば、実行権限で判定する
                flow_data._executable_or_raise()
            else:
                # 参照権限が無ければ例外を送出する
                flow_data._readable_or_raise()

        def mask_unreadble_nodes(flow_data, nodes):
            if nodes is None:
                return
            for node in nodes:
                node_uuid = node.get('uuid')
                if node_uuid is None or node_uuid=='':
                    continue
                if not flow_data._is_readable(node_uuid):
                    node['uuid'] = None
                    node['label'] = '******'
                    # ノードをマスクしたことを示すフラグを追加する
                    node['masked'] = True

        # 権限を判定する
        has_auth_or_raise(self, use_exec_auth)
        # マスキングによって元のflow_json(flowオブジェクトのflow_json)が
        # 書き換わるのを防ぐためコピーを作成する
        import copy
        flow_json = copy.deepcopy(flow_json)
        # 参照権限の無いサブフローやデータソースのラベルとuuidをマスキングする
        nodes = flow_json.get('nodes')
        mask_unreadble_nodes(self, nodes)

        return flow_json

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

    def __eq__(self, other):
        return self._flow_json == other._flow_json

    def __ne__(self, other):
        return self._flow_json != other._flow_json

    def __getitem__(self, key):
        raise Exception(f'FlowDataに"[]"演算子は使えません')

    def __setitem__(self, key, value):
        raise Exception(f'FlowDataに"[]"演算子は使えません')
