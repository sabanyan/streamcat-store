from .flow import Flow
from .flow_data import FlowData

class DataSource(Flow):
    """
    Flowを継承し、かつSQLAlchemyのpolymorphic_identity='flow'の設定は、SQLAlchemyの制約でできない
    そのため、DataSourceクラスを放棄する
    """
    def __init__(self, session, parent, label, store, loader_step):
        """
        コンストラクタ
        """
        # if not Store.exists(store.uuid):
        #     raise Exception('指定されたStoreがライブラリに存在しません')

        # PointとStepの繫がりを探索するFlowVisitorを使えばスマートに、Jsonデータを取得できるだろう
        flow_json = {
            'label': label,
            'nodes': [
                {
                    'id': 'd0',
                    'type': 'store',
                    'uuid': store.uuid,
                    'error': {},
                    'label': store.label,
                    'invalid': {},
                    'makeCache': False,
                    'dataSource': 'csv',
                    'cacheCreatedAt': None
                },
                {
                    'id': 'c1',
                    'args': loader_step.args,
                    'srcs': {
                        loader_step.command.i_ports[0].label : 'd0'
                    },
                    'dsts': {
                        'o': 'd'
                    },
                    'type': 'command',
                    'error': {},
                    'label': 'c1',
                    'commandId': loader_step.command.name,
                    'srcsOrder': [
                        'i'
                    ]
                },
                {
                    'id': 'd',
                    'type': 'frame',
                    'uuid': None,
                    'error': {},
                    'label': 'd',
                    'invalid': {},
                    'makeCache': False,
                    'dataSource': 'csv',
                    'cacheCreatedAt': None
                }
            ],
            'ports': [
                [],
                [
                    {
                        'type': 'frame',
                        'label': 'd',
                        'nodeId': 'd'
                    }
                ]
            ],
            'params': [],
            'creator': self.creator_str,
            'createdAt': self.created_at_str,
            'projectId': None,
            'description': ''
        }
        
        super().__init__(session, parent, label, FlowData(flow_json))