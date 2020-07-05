from kskp.core import Datum

class Vis(Datum):

    TYPE = 'vis'

    def __init__(self, session, parent, label, column_names, matrix, creator=None):
        """
        data : Visデータを指定する
        """
        super().__init__(session, parent, Vis.TYPE, label, creator)

        # Visデータは巨大になり得るので永続化する場合はFrameのようにファイルに保存することになるだろう
        column_names = column_names if column_names is not None else []
        matrix = matrix if matrix is not None else [[]]
        self._data = {'column_names': column_names, 'matrix': matrix}

    @property
    def column_names(self):
        return self._data['column_names']

    @property
    def matrix(self):
        return self._data['matrix']

    @property
    def result(self):
        """
        テストコードで用いる
        """
        result = {}
        result['header'] = self._data['column_names']
        result['reader'] = self._data['matrix']
        return result
        
    def to_html(self):
        result = self.result
        from flask import render_template
        return render_template('visualize/table.html', header=result['header'], reader=result['reader'])


class BokehPlotVis(Vis):
    def __init__(self, session, parent, label, column_names, script, div, creator=None):
        super().__init__(session, parent, label, column_names, None, creator)

        script = script if script is not None else []
        div = div if div is not None else [[]]
        self._data = {'column_names': column_names, 'script': script, 'div': div}

    @property
    def result(self):
        """
        テストコードで用いる
        """
        result = {}
        result['script'] = self._data['script']
        result['div'] = self._data['div']
        return result

    def to_html(self):
        result = self.result
        from flask import render_template
        return render_template('visualize/component.html', script=result['script'], div=result['div'])
        
