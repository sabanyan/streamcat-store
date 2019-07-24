import json
from pathlib import Path
from kskp.store import Library

class FlowLink:
    def __init__(self, flow_uuid):
        self.flow_uuid = flow_uuid

    def resolve(self):
        return self.select_json(self.flow_uuid)

    def select_json(self, flow_uuid):
        """
        uuidを受け取って、json文字列を返す
        TODO: flowのjsonをdbに入れたら変更すること
        """
        flow = Library.load_flow(flow_uuid)
        return json.loads(json.loads(flow.data)['flow'])
