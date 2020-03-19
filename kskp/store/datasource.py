from kskp.store import Datum, Flow

class DataSource(Flow):
    def __init__(self, parent_uuid, label, store, loader_step, creator=None):
        """
        コンストラクタ
        """
        # if not Store.exists(store.uuid):
        #     raise Exception('指定されたStoreがライブラリに存在しません')

        # PointとStepの繫がりを探索するFlowVisitorを使えばスマートに、Jsonデータを取得できるだろう
        flow_data = {
            "label": label,
            "nodes": [
                {
                    "id": "d0",
                    "type": "store",
                    "uuid": store.uuid,
                    "error": {},
                    "label": store.label,
                    "invalid": {},
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": loader_step.args,
                    "srcs": {
                        loader_step.runnable.i_ports[0].name : "d0"
                    },
                    "dsts": {
                        "o": "d"
                    },
                    "type": "command",
                    "error": {},
                    "label": "c1",
                    "commandId": loader_step.runnable.name,
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d",
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d",
                    "invalid": {},
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame",
                        "label": "d",
                        "nodeId": "d"
                    }
                ]
            ],
            "params": [],
            "creator": self.creator_str,
            "createdAt": self.created_at_str,
            "projectId": None,
            "description": ""
        }
        
        super().__init__(parent_uuid, label, flow_data, creator)