# ビジュアライズコマンド
import os
from kskp.core import Command, Port
from kskp.store import List
import nysol.mcmd as nm

ErrMsg={
        '1': "VisualizeInitException"
}

class VisualizersCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'list')]
        self.o_ports = [Port('o', 'vis')]

    def run(self, args, inputs):
        pass

class VisualizersHtml(VisualizersCommand):
    """
    Bokehを使うコマンドと分けたかったのでとりあえず作成
    とりあえず感が半端ない。。。
    """
    def __init__(self):
        super().__init__()

class CsvToTableCommand(VisualizersHtml):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        """
        ListデータをVisデータにして返す
        """
        from kskp.store import ApparentLast
        from kskp.store import Vis

        # 直前のRunsCommandがエラーを返した場合、直後のActivityCommandにエラーを渡す
        if inputs['i'].has_exs:
            return {'o': inputs['i']}

        # 結果はVisに入れて返す
        list_datum = inputs['i'].datum
        column_names = list_datum[0] if len(list_datum) > 0 else []
        matrix = list_datum[1:] if len(list_datum) > 1 else [[]]
        vis = Vis(None, None, 'csv_to_table', column_names, matrix)

        return {'o': ApparentLast(inputs['i'].out_point, vis)}  

class VisualizersBokehPlot(VisualizersCommand):
    """
    Bokehを使うとき用
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        from kskp.store import ApparentLast
        from kskp.store import BokehPlotVis

        # 直前のRunsCommandがエラーを返した場合、直後のActivityCommandにエラーを渡す
        if inputs['i'].has_exs:
            return {'o': inputs['i']}

        list_datum = inputs['i'].datum
        column_names = list_datum[0] if len(list_datum) > 0 else []
        matrix = list_datum[1:] if len(list_datum) > 1 else [[]]
        p = self.plot(args, column_names, matrix)
        script1, div1 = components(p)

        label = self.__class__.__name__
        vis = BokehPlotVis(None, None, label, column_names, script1, div1)

        # とりあえず動くようにするため
        # vis.data = nm.runfunc(lambda : None)

        return {'o': ApparentLast(inputs['i'].out_point, vis)} 

    def direct_product_by_keys(self, df, keys):
        """
        キー項目の直積を求める
        """
        import itertools
        args = {key: df[key].unique().tolist() for key in keys}
        direct_product = list(itertools.product(*list(args.values())))

        results = []
        for seki in direct_product:
            results.append(dict(zip(keys, seki)))

        return results

    def process_df(self, df, direct_product):
        """
        直積で絞り込んだdf群を返す
        """
        df_dict = {}
        for result in direct_product:
            _df = df
            for key, value in result.items():
                _df = _df[_df[key]==value]
            df_dict['-'.join(map(str, list(result.values())))] = _df
        return df_dict

    def _get_proper_column(self, column_names, index):
        if index > len(column_names) -1:
            return column_names[len(column_names) -1]
        else:
            return column_names[index]

    def _infer_data_columns(self, column_names):
        return [self._get_proper_column(column_names, 2)]

    def _infer_time_series_column(self, column_names):
        """
        時間軸になりそうなデータ列を取得する
        """
        return self._get_proper_column(column_names, 3)

    def _infer_x_axis_column(self, column_names):
        """
        X軸になりそうなデータ列を取得する
        """
        return self._get_proper_column(column_names, 3)

    def _infer_y_axis_column(self, column_names):
        """
        Y軸になりそうなデータ列を取得する
        """
        return self._get_proper_column(column_names, 4)

    def _proper_x_size(self):
        """
        X軸のサイズを決定する
        """
        return 1000

    def _proper_y_size(self):
        """
        Y軸のサイズを決定する
        """
        return 600

# グラフ化に必要なものの準備
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import holoviews as hv
import random
import nysol.mcmd as nm
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html,components
from bokeh.palettes import Dark2_5 as palette
from bokeh.layouts import gridplot, column
from bokeh.models import HoverTool, Select, Legend, ColumnDataSource
from bokeh.io import output_file, show
from bokeh.models.callbacks import CustomJS
from bokeh.models import Span
import pprint
from numpy import histogram
import itertools

hv.extension('bokeh')

class CsvToLineGraphCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, column_names, matrix):
        """
        ビジュアライズを描画、保存する。
        """
        # 軸の設定
        x_axis          = args.get('x_axis')
        x_axis_column   = x_axis[0]['column'] # 必須
        x_axis_label    = x_axis[0]['label'] 

        x_axis_format_select = args.get('x_axis_format_select') if args.get('x_axis_format_select') else None
        x_axis_format_custom = args.get('x_axis_format_custom')

        y_axis          = args.get('y_axis')
        y_axis_column   = y_axis[0]['column'] # 必須
        y_axis_label    = y_axis[0]['label']

        # データ系列の設定
        data_column     = args.get('data_column') if args.get('data_column') is not None else []

        # データ表示範囲の設定
        #offset          = int(args.get('offset'))   if args.get('offset')   else 0
        #limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))

        # 初期表示時
        if x_axis_column is None and y_axis_column is None: 
            raise Exception(ErrMsg['1'])

        # dfの作成
        df = pd.DataFrame(matrix, columns=column_names)
        
        # 無効値の置換処理
        invaildIndexNames = df[(df[y_axis_column] == '') | (df[y_axis_column] == 'Na') | (df[y_axis_column] == 'Inf') | (df[y_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)

        invaildIndexNames = df[(df[x_axis_column] == '') | (df[x_axis_column] == 'Na') | (df[x_axis_column] == 'Inf') | (df[x_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)

        # Data Typeの指定

        # 折れ線グラフ（時系列用）
        # 横軸：date
        # 縦軸：float
        # データ系列：string
        timeseries_format_nysol = "%Y%m%d%H%M%S.%f"
        timeseries_format_custom = args.get('x_axis_format_custom')

        if x_axis_format_select == "nysol":
            df[x_axis_column] = pd.to_datetime(df[x_axis_column], format=timeseries_format_nysol)
        elif x_axis_format_select == "float":
            df[x_axis_column] = df[x_axis_column].astype(float)
        elif x_axis_format_select == "custom":
            df[x_axis_column] = pd.to_datetime(df[x_axis_column], format=timeseries_format_custom)   
     

        df[y_axis_column] = df[y_axis_column].astype(float)
        df[data_column] = df[data_column].astype(str)

        hv.extension('bokeh')

        if len(data_column) > 0:
            results = self.direct_product_by_keys(df, data_column)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        # 3. 折れ線の作成
        line_list = {}
        scatter_list = {}
        for label, df in named_dfs.items():
            line_list[label] = hv.Curve(df, x_axis_column, y_axis_column).opts(framewise=True)
            scatter_list[label] = hv.Scatter(df, x_axis_column, y_axis_column).opts(framewise=True, size=5)

        ndoverlay = hv.NdOverlay(line_list)
        scatter = hv.NdOverlay(scatter_list)
        overlay = (ndoverlay * scatter).opts(legend_position='top',
                                                 width=graph_width, height=graph_height,
                                                 xlabel=x_axis_label, ylabel=y_axis_label)


        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(overlay).state

        return plot

class CsvToHistogramCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, column_names, matrix):
        """
        ListデータをVisデータにして返す
        """

        # 軸の設定
        x_axis          = args.get('x_axis')
        x_axis_column   = x_axis[0]['column']
        x_axis_label    = x_axis[0]['label']

        # 縦軸列：頻度
        y_axis_label    = ""

        # データ系列の設定
        data_column     = args.get('data_column') if args.get('data_column') is not None else []

        # データ表示範囲の設定
        #offset          = int(args.get('offset'))   if args.get('offset')   else 0
        #limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        bins            = int(args.get('bins')) if args.get('bins') else None
        
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))
        
        # 初期表示時
        if x_axis_column is None: 
            raise Exception(ErrMsg['1'])

        # dfの作成
        df = pd.DataFrame(matrix, columns=column_names)

        # 無効値の置換処理
        invaildIndexNames = df[(df[x_axis_column] == '') | (df[x_axis_column] == 'Na') | (df[x_axis_column] == 'Inf') | (df[x_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)

        # Data Typeの指定
        # ヒストグラム
        # 横軸：date
        # 縦軸：float
        # データ系列：string

        df[x_axis_column] = df[x_axis_column].astype(float)
        df[data_column] = df[data_column].astype(str)

        hv.extension('bokeh')

        if len(data_column) > 0:
            results = self.direct_product_by_keys(df, data_column)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        # 3. ヒストグラムの作成
        hist_list = {}
        
        for label, df in named_dfs.items():
            hist, edges = np.histogram(df[x_axis_column].tolist(), bins=bins)
            hist_list[label] = hv.Histogram((edges, hist)).opts(muted_alpha=0.1)

        ndoverlay = hv.NdOverlay(hist_list).opts(legend_position='top',
                                                 width=graph_width, height=graph_height,
                                                 xlabel=x_axis_label, ylabel=y_axis_label)

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state
        
        return plot

    def _infer_bins_columns(self, column_names):
        """
        Binsになりそうなデータ列を取得する
        """
        return [self._get_proper_column(column_names, 4)]

class CsvToBoxplotCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()
        
    def plot(self, args, column_names, matrix):
        """
        ListデータをVisデータにして返す
        """
        # 縦軸列：観測値
        y_axis          = args.get('y_axis')
        y_axis_column   = y_axis[0]['column']
        y_axis_label    = y_axis[0]['label']

        x_axis_label    = ""

        # データ系列の設定
        data_column     = args.get('data_column')   if args.get('data_column') is not None else []

        # データ表示範囲の設定
        #offset          = int(args.get('offset'))   if args.get('offset')   else 0
        #limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        bins            = int(args.get('bins')) if args.get('bins') else None
        
        # グラフサイズの設定
        graph_width     = int(args.get('width')) if args.get('width') else self._proper_x_size()
        graph_height    = int(args.get('height')) if args.get('height') else self._proper_y_size()

        graph_title     = ""

        # 初期表示時
        if y_axis_column is None: 
            raise Exception(ErrMsg['1'])

        # NysolPythonの結果をpandasのDataFrameに変換する
        # dfの作成
        df = pd.DataFrame(matrix, columns=column_names)
        
        # Data Typeの指定
        # 箱ひげ図
        # 縦軸：float
        # データ系列：string

        # 無効値の置換処理
        invaildIndexNames = df[(df[y_axis_column] == '') | (df[y_axis_column] == 'Na') | (df[y_axis_column] == 'Inf') | (df[y_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)

        df[y_axis_column] = df[y_axis_column].astype(float)
        df[data_column] = df[data_column].astype(str)

        boxwhisker = hv.BoxWhisker(df, kdims=data_column, vdims=y_axis_column, label=graph_title)
        boxwhisker.opts(width=graph_width, height=graph_height, xlabel=x_axis_label, ylabel=y_axis_label)

        renderer = hv.renderer('bokeh')
        plot=renderer.get_plot(boxwhisker).state

        return plot

class CsvToScatterCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, column_names, matrix):
        """
        ListデータをVisデータにして返す
        """
        # 軸の設定
        x_axis          = args.get('x_axis')
        x_axis_column   = x_axis[0]['column']
        x_axis_label    = x_axis[0]['label']

        y_axis          = args.get('y_axis')
        y_axis_column   = y_axis[0]['column']
        y_axis_label    = y_axis[0]['label']

        # データ系列の設定
        data_column     = args.get('data_column')   if args.get('data_column') is not None else []

        # データ表示範囲の設定
        #offset          = int(args.get('offset'))   if args.get('offset')   else 0
        #limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        withoutContourLine  = args.get('withoutContourLine') if args.get('withoutContourLine') else False
        
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(withoutContourLine)
        pp.pprint("-----------------------")
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))

        # 初期表示時
        if x_axis_column is None and y_axis_column is None: 
            raise Exception(ErrMsg['1'])

        # dfの作成
        df = pd.DataFrame(matrix, columns=column_names)

        # Data Typeの指定
        # 散布図
        # 横軸：float
        # 縦軸：float
        # データ系列：string

        # 無効値の置換処理
        invaildIndexNames = df[(df[y_axis_column] == '') | (df[y_axis_column] == 'Na') | (df[y_axis_column] == 'Inf') | (df[y_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)

        invaildIndexNames = df[(df[x_axis_column] == '') | (df[x_axis_column] == 'Na') | (df[x_axis_column] == 'Inf') | (df[x_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)
        
        df[x_axis_column] = df[x_axis_column].astype(float)
        df[y_axis_column] = df[y_axis_column].astype(float)
        df[data_column] = df[data_column].astype(str)
        hv.extension('bokeh')
        
        if len(data_column) > 0:
            results = self.direct_product_by_keys(df, data_column)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df
        
        # 3. 散布図の作成
        scatter_list = {}
        for label, _df in named_dfs.items():
            scatter_list[label] = hv.Scatter(_df, x_axis_column, vdims=[y_axis_column]).opts(muted_alpha=0.1, size=6)

        ndoverlay = hv.NdOverlay(scatter_list).opts(legend_position='top',
                                                 width=int(graph_width), height=int(graph_height),
                                                 xlabel=x_axis_label, ylabel=y_axis_label)

        if not withoutContourLine:
            b = hv.Bivariate(df[[x_axis_column, y_axis_column]]).opts(show_legend=False, bandwidth=0.5, axiswise=True, line_width=2, colorbar=False, alpha=0.1)
            ndoverlay = ndoverlay * b

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state
        
        return plot

class CsvToRepetitivieWaveCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, column_names, matrix):
        # 軸の設定
        event = args.get('event') if args.get('event') else None

        x_axis          = args.get('x_axis')
        x_axis_column   = x_axis[0]['column']
        x_axis_label    = x_axis[0]['label']

        y_axis          = args.get('y_axis')
        y_axis_column   = y_axis[0]['column']
        y_axis_label    = y_axis[0]['label']

        # データ系列の設定
        data_column     = args.get('data_column')   if args.get('data_column') else []
        group           = args.get('group') if args.get('group') else None

        # グラフ表示要素の設定
        disableTooltips = args.get('disableTooltips') if args.get('disableTooltips') else False
        disableMarker = args.get('disableMarker') if args.get('disableMarker') else False
        disableStatics = args.get('disableStatics') if args.get('disableStatics') else False
        disableEvent = args.get('disableEvent') if args.get('disableEvent') else False
        statics = args.get('statics') if args.get('statics') else None
        
        # グラフサイズの設定
        graph_width = args.get('width')
        graph_height = args.get('height')

        # 初期表示時
        if x_axis_column is None and y_axis_column is None: 
            raise Exception(ErrMsg['1'])

        # 必須項目チェック
        if x_axis_column is None or y_axis_column is None or group is None or statics is None:
            return 

        # dfの作成
        df = pd.DataFrame(matrix, columns=column_names)

        # 無効値の置換処理
        invaildIndexNames = df[(df[y_axis_column] == '') | (df[y_axis_column] == 'Na') | (df[y_axis_column] == 'Inf') | (df[y_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)

        invaildIndexNames = df[(df[x_axis_column] == '') | (df[x_axis_column] == 'Na') | (df[x_axis_column] == 'Inf') | (df[x_axis_column] == 'NaN')].index
        df.drop(invaildIndexNames , inplace=True)
 
        # Data Typeの指定
        # Visualizers
        # 横軸：float
        # 縦軸：float
        # データ系列：string
        df[x_axis_column] = df[x_axis_column].astype(float)
        df[y_axis_column] = df[y_axis_column].astype(float)
        df[data_column] = df[data_column].astype(str)

        # グループ属性の初期化
        unique_group = None 
        if group is not None:
            unique_group = df[group].unique().tolist()

        # 起点の初期化
        xs_event = None
        if event is not None:
            queryStr = "{0}=='{1}'".format(event, "0")
            result_df = df.query(queryStr)
            result_df[x_axis_column] = result_df[x_axis_column].astype(float)
            xs_event = result_df[x_axis_column].unique().tolist()
            
        # plots
        plots = []

        # 反復波形図（標準）
        named_dfs = {}
        if data_column is not None and len(data_column) > 0:
            results = self.direct_product_by_keys(df, data_column)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs['all'] = df
                
        # source
        source = {}
        for label, n_df in named_dfs.items():
            xs = n_df[x_axis_column].tolist()
            ys = n_df[y_axis_column].tolist()

            groups = n_df[group].tolist() if group else None
            labels = [label] * (len(n_df.index))

            keys = ["x","y"]
            values = [xs,ys]

            if groups:
                keys.append("group")
                values.append(groups)
            if labels:
                keys.append("label")
                values.append(labels)

            source[label] = self.toColumnDataSource(keys, values)

        # plot
        title = "反復波形図"
        tools = "pan,wheel_zoom,box_zoom,reset,save,box_select"
        tooltips = None
        if disableTooltips != True:
            tooltips = [
                ("凡例", "@label"),
                (x_axis_column, "@x"),
                (y_axis_column, "@y")
            ]
            if group is not None:
                tooltips.append((group, "@group"))

        plot = figure(
            title=title,
            tools=tools,
            tooltips=tooltips,
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label
        )

        # plot
        colors = self.get_colors(len(source))
        for label, color in zip(source,colors):
            # 線
            plot.line('x', 'y', source=source[label], legend=label, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2, line_width=2)
            # 点
            if disableMarker != True:
                plot.circle('x', 'y', source=source[label], legend=label, color=color, alpha=0.9, muted_color=color, muted_alpha=0.2, size=5)
        
        # 起点
        if disableEvent != True and xs_event is not None:
            for x in xs_event:
                s = Span(location= x,
                                dimension='height', line_color='black',
                                line_dash='dashed', line_width=3, line_alpha=0.3)
                plot.add_layout(s)

        # plot設定
        plot.legend.location = "top_left"
        plot.legend.click_policy = "mute"

        # 反復波形図(統計量)
        statics_plot = None
        if disableStatics == False and statics is not None:
            k = x_axis_column
            f = y_axis_column
            c = statics #"min,mean,max,qtile1,median,qtile3"
            i = df.values.tolist()
            i.insert(0,list(df.columns))

            dtype = "{}:float".format(x_axis_column)
            result = None
            result <<= nm.msummary(i=i, k=k, f=f, c=c)
            result <<= nm.writelist(header=True)
            result = result.run()

            name=result.pop(0)
            statics_df = pd.DataFrame(result,columns=name)
            # Data Typeの指定
            # Visualizers
            # 横軸：float
            statics_df[k] = statics_df[k].astype(float)
            statics_keys = c.split(',')
            for key in statics_keys:
                statics_df[key] = statics_df[key].astype(float)

            # sort
            statics_df = statics_df.sort_values(by = k)

            # source
            statics_source = {}
            for key in statics_keys:
                xs = statics_df[k].tolist()
                ys = statics_df[key].tolist()
                label = [key] * (len(xs))
                keys = ["x","y","label"]
                values = [xs,ys,label]

                statics_source[key] = dict(zip(keys, values))
                
            # plot
            title = "反復波形図(統計量)"
            tools = "pan,wheel_zoom,box_zoom,reset,save,box_select"
            tooltips = None
            if disableTooltips != True:
                tooltips = [
                    ("凡例", "@label"),
                    (x_axis_column, "@x"),
                    (y_axis_column, "@y")
                ]

            statics_plot = figure(
                title=title,
                tools=tools,
                tooltips=tooltips,
                x_axis_label=x_axis_label,
                y_axis_label=y_axis_label
            )
            # plot
            colors = self.get_colors(len(statics_source))
            for label, color in zip(statics_source,colors):
                # 線
                statics_plot.line('x', 'y', source=ColumnDataSource(data=statics_source[label]), legend=label, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2,line_width=2)
                # 点
                if disableMarker != True:
                    statics_plot.circle('x', 'y', source=ColumnDataSource(data=statics_source[label]), legend=label, color=color, alpha=0.9, muted_color=color, muted_alpha=0.2, size=5)
                # 面
                keys = list(statics_source.keys())
                length = len(keys)
                for index, key in enumerate(keys):
                    if (index + 1) < length:
                        x = statics_source[key]['x']
                        y1 = statics_source[key]['y']
                        y2 = statics_source[keys[index + 1]]['y']
                        statics_plot.varea(x=x, y1=y1, y2=y2, fill_color='#cccccc', alpha=0.3)

            # 起点
            if disableEvent != True and xs_event is not None:
                for x in xs_event:
                    s = Span(location= x, dimension='height', line_color='black', line_dash='dashed', line_width=3, line_alpha=0.3)
                statics_plot.add_layout(s)

            # plot設定
            statics_plot.legend.location = "top_left"
            statics_plot.legend.click_policy = "mute"
                   
        # select(グループ属性)
        select = None
        if group is not None and unique_group is not None:
            select = self.get_select(plot, group, unique_group)
            plots.append(select)
        plots.append(plot)
        if statics_plot is not None:
            plots.append(statics_plot)
        
        return gridplot(plots, ncols=1, plot_width=graph_width, plot_height=graph_height, toolbar_location="right")
    
    def toColumnDataSource(self, keys, values):  
        return ColumnDataSource(data=dict(zip(keys, values)))

    def get_colors(self, size):
        from bokeh.palettes import Dark2_5 as palette
        i = 0
        colors = []
        for d in itertools.cycle(palette):
            if i >= size:
                break
            colors.append(d)
            i = i + 1

        return colors

    def get_select(self, plot, group, unique_group):
        values = unique_group
        values.insert(0, '')

        s = Select(value=values[0], title=group, options=values, width=120)
        callBack = CustomJS(args=dict(plot=plot, select=s), code="""
            var value = select.value
            var renderers = plot.renderers
            if (!renderers) return

            renderers.forEach(r => {
                try {
                    if (value === "") {
                        r.muted = false
                    } else if(r.data_source.data.group[0] === value) {
                        r.muted = false
                    } else {
                        r.muted = true
                    } 
                } catch(e) {
                    console.log(e)
                }
            })
        """)
        s.js_on_change('value', callBack)


        return s
    
    def doMsummary(self, df, k, f, c):

        i = df.values.tolist()
        i.insert(0,list(df.columns))

        result = None
        result <<= nm.msummary(i=i, k=k, f=f, c=c).writelist(header=True)
        result = result.run()

        name = result.pop(0)
        result_df = pd.DataFrame(result,columns=name)

        return result_df


class CsvToTimeCompressionCommand(VisualizersBokehPlot):

    def __init__(self):
        super().__init__()

    def plot(self, args, column_names, matrix):

        # 軸の設定
        x_axis         = args.get('x_axis')
        x_axis_column  = x_axis[0]['column']
        x_axis_label   = x_axis[0]['label']

        y_axis         = args.get('y_axis')
        y_axis_column  = y_axis[0]['column']
        y_axis_label   = y_axis[0]['label']

        # データ系列の設定
        data     = args.get('data')   if args.get('data') is not None else []

        # データ表示範囲の設定
        #offset          = int(args.get('offset'))   if args.get('offset')   else 0
        #limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        division        = args.get('division')
        statics         = args.get('statics')
        display_pattern = args.get('display_pattern')
        
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))

        # df
        df = pd.DataFrame(matrix, columns=column_names)
        df[y_axis_column] = df[y_axis_column].astype(float)
        df[x_axis_column] = df[x_axis_column].astype(float)

        # title
        df_x_minmax = self.doMsummary(df, None, x_axis_column, "min,max")
        df_y_minmax = self.doMsummary(df, None, y_axis_column, "min,max")

        x_min = df_x_minmax.iat[0, 1]
        x_max = df_x_minmax.iat[0, 2]

        y_min = df_y_minmax.iat[0, 1]
        y_max = df_y_minmax.iat[0, 2]

        if len(data) > 0:
            results = self.direct_product_by_keys(df, data)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df
   
        def rangesToPoints(df, column):
            for index, row in df.iterrows():
                array = df.at[index, column].split("_")
                df.at[index, column] = '0' if array[0] == '' else array[0]

        staticsArray = statics.split(",")
        source = {}
        for label, _df in named_dfs.items():

            if _df.empty == True:
                continue
                            
            source[label] = {}

            # 分割
            result_column = x_axis_column + "_"
            f = "{}:{}".format(x_axis_column, result_column)
            df_bucket = self.doMbucket(_df, None, f, division)

            # min, max
            df_x_minmax = self.doMsummary(_df, None, x_axis_column, "min,max")
            df_y_minmax = self.doMsummary(_df, None, y_axis_column, "min,max")
            x_min = df_x_minmax.iat[0, 1]
            x_max = df_x_minmax.iat[0, 2]

            y_min = df_y_minmax.iat[0, 1]
            y_max = df_y_minmax.iat[0, 2]

            source[label]["x_range"] = [float(x_min),float(x_max)]
            source[label]["y_range"] = [float(y_min),float(y_max)]

            # 統計量
            df_summary = self.doMsummary(df_bucket, result_column, y_axis_column, statics)
            rangesToPoints(df_summary, result_column)
            df_summary = df_summary.sort_values(result_column)

            source[label][result_column] = df_summary[result_column].tolist()
            for s in staticsArray:
                source[label][s] = df_summary[s].tolist()
 
        # Graph Plot
        plots = []
        for g in source:
            title = "時間圧縮図:{}、 期間:{} ~ {}".format(g, source[g]["x_range"][0], source[g]["x_range"][1])
            tools = "pan,wheel_zoom,box_zoom,reset,save,box_select"
            plot = figure(
                title=title,
                tools=tools,
                x_range=source[g]["x_range"],
                y_range=source[g]["y_range"],
                x_axis_label=x_axis_label,
                y_axis_label=y_axis_label
            )
            colors = self.get_colors(len(staticsArray))
            index = 0
            for index in range(len(staticsArray)):
                color = colors[index]
                statics = staticsArray[index]
                plot.line(source[g][result_column], source[g][statics], legend=statics, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2)
                if display_pattern == "hatch" and index + 1 < len(staticsArray):
                        x = source[g][result_column]
                        y1 = source[g][staticsArray[index]]
                        y2 = source[g][staticsArray[index + 1]]
                        plot.varea(x=x, y1=y1, y2=y2, fill_color='#cccccc', alpha=0.5)  

            plot.legend.location = "top_left"
            plot.legend.click_policy = "mute"
            plots.append(plot)

        result = gridplot(plots, ncols=1, plot_width=graph_width, plot_height=graph_height, toolbar_location="right") 
        
        return result
    
    def get_colors(self, size):
        i = 0
        colors = []
        for d in itertools.cycle(palette):
            if i >= size:
                break
            colors.append(d)
            i = i + 1

        return colors

    def doMsummary(self, df, k, f, c):

        i = df.values.tolist()
        i.insert(0,list(df.columns))

        result = None
        result <<= nm.msummary(i=i, k=k, f=f, c=c).writelist(header=True)
        result = result.run()

        name = result.pop(0)
        result_df = pd.DataFrame(result,columns=name)

        return result_df

    def doMbucket(self, df, k, f, n, F="1", rng=True):
   
        i = df.values.tolist()
        i.insert(0,list(df.columns))

        result = None
        result <<= nm.mbucket(i=i, k=k, n=n, f=f, F=F, rng=rng).writelist(header=True)
        result = result.run()
        
        name = result.pop(0)
        result_df = pd.DataFrame(result,columns=name)

        return result_df