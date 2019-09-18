import json
from pathlib import Path

class FlowLink:
    def __init__(self, flow_uuid):
        self.flow_uuid = flow_uuid

    def resolve(self):
        return self.select_json(self.flow_uuid)[1]

    def select_json(self, flow_uuid):
        """
        uuidを受け取って、json文字列を返す
        """
        from kskp.store import Flow
        flow = Flow.find_by_uuid(flow_uuid)
        return flow.flow_data
