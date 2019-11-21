from kskp.core import Datum

class Vis(Datum):

    TYPE = 'vis'

    def __init__(self, parent_uuid, label, creator=None):
        """
        data : Visデータを指定する
        """
        super().__init__(parent_uuid, Vis.TYPE, label, creator)

        # data列の値を作成する
        self.data = None
        self.nysol_result = []
        # 列名一覧を保持する
        self.column_names = []

    @property
    def result(self):
        """
        テストコードで用いる
        """
        result = {}
        result['header'] = self.nysol_result[0]
        result['reader'] = self.nysol_result[1:]
        return result
        
    def to_html(self):
        result = {}
        result['header'] = self.nysol_result[0]
        result['reader'] = self.nysol_result[1:]

        from flask import render_template
        return render_template('visualize/table.html', header=result['header'], reader=result['reader'])


class BokehPlotVis(Vis):
    def __init__(self, parent_uuid, label, creator=None):
        super().__init__(parent_uuid, label, creator)
        self.script = None
        self.div = None

    @property
    def result(self):
        """
        テストコードで用いる
        """
        result = {}
        result['script'] = self.script
        result['div'] = self.div
        return result

    def to_html(self):
        result = {}
        result['script'] = self.script
        result['div'] = self.div

        from flask import render_template
        return render_template('visualize/component.html', script=result['script'], div=result['div'])
        
