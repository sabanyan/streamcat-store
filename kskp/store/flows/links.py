import json
from pathlib import Path

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
        from kskp.store import FLOW_PATH

        # 実ファイルの場合は、ファイル名がuuidとなっている
        flow_path = Path(FLOW_PATH) / (flow_uuid + '.json')

        if not flow_path.exists():
            raise Exception(f"存在しないflow_uuid'{flow_uuid}'が指定されています")

        with open(flow_path) as f:
            return json.load(f)
