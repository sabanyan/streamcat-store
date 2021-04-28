from typing import Callable

class FlowData():
    """
    Flowデータを表す
    """
    # Flow Jsonの定義
    FLOW_JSON_SCHEMA = {
        "title" : "Flow JSON Schema",
        "description" : "This is a schema that verifies Flow JSON.",
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$ref': '#/definitions/Flow',
        'definitions': {
            'Flow': {
                'type': 'object',
                'required': [],
                'additionalProperties': False,
                'properties': {
                    'label': {
                        'type': ['null', 'string']
                    },
                    'description': {
                        'type': ['null', 'string']
                    },
                    'creator': {
                        'type': ['null', 'string']
                    },
                    'createdAt': {
                        'type': ['null', 'string']
                    },
                    'projectId': {
                        'type': ['null', 'integer']
                    },
                    'datasource':{
                        'type': 'object',
                        '$ref': '#/definitions/FrameNode',
                    },
                    'nodes': {
                        'type': 'array',
                        'items': {
                            'anyOf': [
                                {
                                    'type': 'object',
                                    '$ref': '#/definitions/FrameNode'
                                },
                                {
                                    'type': 'object',
                                    '$ref': '#/definitions/CommandNode'
                                },
                                {
                                    'type': 'object',
                                    '$ref': '#/definitions/FlowNode'
                                },
                                {
                                    'type': 'object',
                                    '$ref': '#/definitions/NoteNode'
                                },
                                {
                                    'type': 'object',
                                    '$ref': '#/definitions/IntNode'
                                }
                            ]
                        }
                    },
                    'params': {
                        'type': 'array',
                        'items': {
                            '$ref': '#/definitions/Param'
                        }
                    },
                    'ports': {
                        'type': 'array',
                        'maxItems': 2,
                        'minItems': 2,
                        'items': {
                            'type': 'array',
                            'items': {
                                '$ref': '#/definitions/Port'
                            }
                        }
                    }
                }
            },
            'FrameNode': {
                'type': 'object',
                'required': [
                    'id',
                    'type'
                ],
                'additionalProperties': False,
                'properties': {
                    'id': {
                        '$ref': '#/definitions/id'
                    },
                    'label': {
                        'type': 'string'
                    },
                    'type': {
                        'enum': ['frame', 'store', 'int']
                    },
                    'uuid': {
                        'anyOf': [
                            {
                                'type': 'null'
                            },
                            {
                                '$ref': '#/definitions/uuid'
                            }
                        ]
                    },
                    'value': {
                        'anyOf': [
                            {
                                'type': 'array',
                                'items': {
                                    'type': 'array',
                                    'items': {
                                        'type': ['null', 'string', 'number', 'boolean']
                                    }
                                }
                            },
                            {
                                'type': 'null'
                            }
                        ]
                    },
                    'makeCache': {
                        'type': 'boolean'
                    },
                    'dataSource': {
                        'type': 'string',
                        'pattern': '^[0-9a-zA-Z_]+$'
                    },
                    'cacheCreatedAt': {
                        'type': ['null', 'string']
                    },
                    'position': {
                        '$ref': '#/definitions/Position'
                    },
                    'size': {
                        '$ref': '#/definitions/Size'
                    },
                    'error': {
                        '$ref': '#/definitions/Error'
                    },
                    'invalid': {
                        '$ref': '#/definitions/Error'
                    }
                }
            },
            'CommandNode': {
                'type': 'object',
                'required': [
                    'id',
                    'type',
                    'commandId'
                ],
                'additionalProperties': False,
                'properties': {
                    'id': {
                        '$ref': '#/definitions/id'
                    },
                    'label': {
                        'type': 'string'
                    },
                    'type': {
                        'const': 'command'
                    },
                    'commandId': {
                        'type': 'string',
                        'pattern': '^[0-9a-zA-Z_]+$'
                    },
                    'args': {
                        '$ref': '#/definitions/Args'
                    },
                    'srcs': {
                        '$ref': '#/definitions/Srcs'
                    },
                    'dsts': {
                        '$ref': '#/definitions/Dsts'
                    },
                    'position': {
                        '$ref': '#/definitions/Position'
                    },
                    'size': {
                        '$ref': '#/definitions/Size'
                    },
                    'srcsOrder': {
                        'type': 'array',
                        'items': {
                            '$ref': '#/definitions/portId'
                        }
                    },
                    'error': {
                        '$ref': '#/definitions/Error'
                    },
                    'invalid': {
                        '$ref': '#/definitions/Error'
                    }
                }
            },
            'FlowNode': {
                'type': 'object',
                'required': [
                    'id',
                    'type',
                ],
                'additionalProperties': False,
                'properties': {
                    'id': {
                        '$ref': '#/definitions/id'
                    },
                    'label': {
                        'type': 'string'
                    },
                    'type': {
                        'const': 'flow'
                    },
                    'uuid': {
                        'anyOf': [
                            {
                                'type': 'null'
                            },
                            {
                                '$ref': '#/definitions/uuid'
                            }
                        ]
                    },
                    'flow': {
                        # Flowリテラル
                        '$ref': '#/definitions/Flow'
                    },
                    'args': {
                        '$ref': '#/definitions/Args'
                    },
                    'srcs': {
                        '$ref': '#/definitions/Srcs'
                    },
                    'dsts': {
                        '$ref': '#/definitions/Dsts'
                    },
                    'masked': {
                        'type': 'boolean'
                    },
                    'position': {
                        '$ref': '#/definitions/Position'
                    },
                    'size': {
                        '$ref': '#/definitions/Size'
                    },
                    'srcsOrder': {
                        'type': 'array',
                        'items': {
                            '$ref': '#/definitions/portId'
                        }
                    },
                    'error': {
                        '$ref': '#/definitions/Error'
                    },
                    'invalid': {
                        '$ref': '#/definitions/Error'
                    }
                }
            },
            'NoteNode': {
                'type': 'object',
                'required': [
                    'id',
                    'type',
                    'title'
                ],
                'additionalProperties': False,
                'properties': {
                    'id': {
                        '$ref': '#/definitions/id'
                    },
                    'label': {
                        'type': 'string'
                    },
                    'type': {
                        'const': 'note'
                    },
                    'title': {
                        'type': 'string'
                    },
                    'content': {
                        'type': 'string'
                    },
                    'fontSize': {
                        'type': 'number',
                        'minimum': 0
                    },
                    'color': {
                        'type': 'string'
                    },
                    'position': {
                        '$ref': '#/definitions/Position'
                    },
                    'size': {
                        '$ref': '#/definitions/Size'
                    },
                    'error': {
                        '$ref': '#/definitions/Error'
                    },
                    'invalid': {
                        '$ref': '#/definitions/Error'
                    }
                }
            },
            'IntNode': {
                'type': 'object',
                'required': [
                    'id',
                    'type',
                    'value'
                ],
                'additionalProperties': False,
                'properties': {
                    'id': {
                        '$ref': '#/definitions/id'
                    },
                    'label': {
                        'type': 'string'
                    },
                    'type': {
                        'const': 'int'
                    },
                    'value': {
                        'anyOf': [
                            {
                                'type': 'array',
                                'maxItems': 1,
                                'minItems': 1,
                                'items': {
                                    'type': 'array',
                                    'maxItems': 1,
                                    'minItems': 1,
                                    'items': {
                                        'type': ['null', 'string', 'number', 'boolean']
                                    }
                                }
                            }
                        ]
                    },
                    'uuid': {
                        'const': 'null'
                    }
                }
            },
            'Args': {
                'type': 'object',
                'required': [],
                'additionalProperties': {
                    'type': ['null', 'string', 'number', 'boolean', 'array', 'object']
                },
                'propertyNames': {
                    'type': 'string'
                }
            },
            'Param': {
                'type': 'object',
                'required': [
                    'name',
                    'type'
                ],
                'additionalProperties': False,
                'properties': {
                    'name': {
                        'type': 'string'
                    },
                    'label': {
                        'type': 'string'
                    },
                    'type': {
                        'type': 'string'
                    },
                    'uuid': {
                        '$ref': '#/definitions/uuid'
                    }
                }
            },
            'Port': {
                'type': 'object',
                'required': [
                    'label',
                    'nodeId',
                    'type'
                ],
                'additionalProperties': False,
                'properties': {
                    'label': {
                        '$ref': '#/definitions/portId'
                    },
                    'nodeId': {
                        '$ref': '#/definitions/id'
                    },
                    'type': {
                        'type': 'string'
                    }
                }
            },
            'Srcs': {
                'type': 'object',
                'required': [],
                'additionalProperties': {
                    '$ref': '#/definitions/id'
                },
                'propertyNames': {
                    '$ref': '#/definitions/portId'
                }
            },
            'Dsts': {
                'type': 'object',
                'required': [],
                'additionalProperties': {
                    '$ref': '#/definitions/id'
                },
                'propertyNames': {
                    '$ref': '#/definitions/portId'
                }
            },
            'Position': {
                'type': 'object',
                'required': [
                    'x',
                    'y'
                ],
                'additionalProperties': False,
                'properties': {
                    'x': {
                        'type': 'number',
                        'minimum': 0
                    },
                    'y': {
                        'type': 'number',
                        'minimum': 0
                    }
                }
            },
            'Size': {
                'type': 'object',
                'required': [
                    'height',
                    'width'
                ],
                'additionalProperties': False,
                'properties': {
                    'width': {
                        'type': 'number',
                        'minimum': 0
                    },
                    'height': {
                        'type': 'number',
                        'minimum': 0
                    }
                }
            },
            'Error': {
                'type': 'object',
                'additionalProperties': False,
                'patternProperties': {
                    '^[0-9a-zA-Z_]+$': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        }
                    }
                }
            },
            'id': {
                'id': 'id',
                'type': 'string',
                'pattern': '^[0-9a-zA-Z_]+$'
            },
            'uuid': {
                'id': 'uuid',
                'type': 'string',
                # The format of uuid was added in JSON Schema spec version 2019-09 (previously known as draft-08). 
                'pattern': '^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'
            },
            'portId': {
                'id': 'portId',
                'type': 'string'
                # ポートidはラベルとしても用いられている
                # 'pattern': '^[0-9a-zA-Z_*]+$'
            }
        }
    }

    def __init__(self,
                 flow_json:dict = {},
                 is_readable:Callable[[str],bool] = None,
                 is_executable:Callable[[str],bool] = None,
                 readable_or_raise:Callable[[],None] = None, 
                 executable_or_raise:Callable[[],None] = None):
        self._flow_json = flow_json

        # readable_or_raise()が指定されない場合は権限判定をしない
        true_func = lambda uuid: True
        empty_func = lambda: None
        self._is_readable = is_readable or true_func
        self._is_executable = is_executable or true_func
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

    # @property
    # def ports(self) -> list:
    #     return self._flow_json.get('ports')

    @property
    def i_ports(self) -> list:
        ports = self._flow_json.get('ports')
        if ports is None:
            return []
        return ports[0]

    @property
    def o_ports(self) -> list:
        ports = self._flow_json.get('ports')
        if ports is None:
            return []
        return ports[1]

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
            # フローエディタでノードの削除・追加を行うことで、Nodeのidは再利用されることに注意すること
            # その場合、再利用されたidでもmaskedキーはないノードなので、マスキング解除の対象ノードには
            # ならない

            # フローエディタでuuidがNoneのノードを追加できないので、uuidがNoneのノードはマスキング
            # されたノードだと判断できるが、何らかの不具合によりNoneになる可能性を考慮して、
            # maskedフラグを導入し、これで判断する。なお、確実に判断するためuuidがNoneの条件も含める
            if not node.get('masked') or node.get('uuid') is not None:
                continue

            # 前の版のフローJsonから同じidのノードを取得する
            original_node = FlowData._find_node(prev_ver_nodes, node['id'])

            if original_node is not None and not original_node.get('masked'):
                # マスクを外す
                node['uuid'] = original_node.get('uuid')
                node['label'] = original_node.get('label')

            # ノードをマスクしたことを示すフラグを削除する
            del node['masked']

    def to_json(self, contains_nodes=True, minimize=False):
        if contains_nodes:
            flow_json = self._authorize(self._flow_json)
            if minimize:
                flow_json = self._minimize(flow_json)
            return flow_json
        else:
            return {
                'label': self.label,
                'description': self.description,
                'creator': self.creator,
                'createdAt': self.created_at,
                'params': self.params,
                'ports': [self.i_ports, self.o_ports]
            }

    def valid_flow_json_or_raise(self):
        """
        フローJSONの書式に従っていない場合は例外を送出する
        """
        from jsonschema import validate, ValidationError
        try:
            validate(self._flow_json, FlowData.FLOW_JSON_SCHEMA)
        except ValidationError as e:
            raise

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
                return

    def _unset_cache(self, node_id):
        """
        指定するノードidのキャッシュを解除する
        """
        if 'nodes' not in self._flow_json:
            return None

        for node in self._flow_json.get('nodes'):
            if node['id'] == node_id:
                cache_uuid = node.get('uuid')
                if cache_uuid is None:
                    return None
                # ノードからキャッシュを解除する
                node['uuid'] = None
                node['cacheCreatedAt'] = None
                # ノードidは重複しないので1つ解除したら処理を終了する
                return cache_uuid
        return None

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

    def _minimize(self, flow_json):
        nodes = flow_json.get('nodes')
        if nodes is None:
            return flow_json
        for node in nodes:
            if node.get('uuid') is None:
                node.pop('uuid', None)
            if node.get('makeCache') == False:
                node.pop('makeCache', None)
            if node.get('cacheCreatedAt') is None:
                node.pop('cacheCreatedAt', None)
            node.pop('position', None)
            node.pop('size', None)
            node.pop('error', None)
            node.pop('invalid', None)
            node.pop('srcsOrder', None)
        return flow_json

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

        def mask_unreadble_nodes(flow_data, nodes, use_exec_auth):
            if nodes is None:
                return
            for node in nodes:
                node_uuid = node.get('uuid')
                if node_uuid is None or node_uuid=='':
                    continue
                elif node.get('type')=='flow' and use_exec_auth:
                    if not flow_data._is_executable(node_uuid):
                        # フロー実行のための参照であれば、ノードのマスキングではなく例外を送出する
                        from kskp.store.auth import NotAuthorizedException
                        raise NotAuthorizedException(f'共有フロー({node.get("id")})の実行権限がありません')
                elif not flow_data._is_readable(node_uuid):
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
        mask_unreadble_nodes(self, nodes, use_exec_auth)

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

    def __repr__(self):
        return self.label or ''

    def __eq__(self, other):
        return self._flow_json == other._flow_json

    def __ne__(self, other):
        return self._flow_json != other._flow_json

    def __getitem__(self, key):
        raise Exception(f'FlowDataに"[]"演算子は使えません')

    def __setitem__(self, key, value):
        raise Exception(f'FlowDataに"[]"演算子は使えません')
