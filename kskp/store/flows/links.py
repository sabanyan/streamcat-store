import json
from pathlib import Path

class FlowLink:
    def __init__(self, flow_uuid):
        self.flow_uuid = flow_uuid
        self.flow = None

    def resolve(self):
        if self.flow is None:
            self.flow = self._select_flow(self.flow_uuid)
        return self.flow.flow_data

    def resolve_label(self):
        if self.flow is None:
            self.flow = self._select_flow(self.flow_uuid)
        return self.flow.label

    def _select_flow(self, flow_uuid):
        """
        uuidを受け取って、json文字列を返す
        """
        from kskp.store import Flow
        flow = Flow.find_by_uuid(flow_uuid)
        return flow
