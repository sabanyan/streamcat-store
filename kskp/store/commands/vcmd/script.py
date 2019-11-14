# ビジュアライズコマンド
import os

from kskp.core import Command, Port
# from kskp.store import Library

import nysol.mcmd as nm

class VisualizersCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'list')]
        self.o_ports = [Port('o', 'preview')]

    def run(self, args, inputs):
        pass

class VisualizersHtml(VisualizersCommand):
    """
    Bokehを使うコマンドと分けたかったのでとりあえず作成
    とりあえず感が半端ない。。。
    """
    def __init__(self):
        super().__init__()

class CsvToTableCommand2(VisualizersHtml):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        """
        csvのファイルパスから、
        HTMLのテーブル形式にして返す
        """
        # # offset対応
        # offset = int(args.get('offset')) if args.get('offset') else 0
        # limit = int(args.get('limit')) if args.get('limit') else 999999
        # offset_limit = offset + limit

        # nysol_result = []
        # # inputs['i']にはNysolPythonコマンドが来る
        # cmd = inputs['i']
        # cmd <<= nm.msel(c=f'{offset}<=line() && line()<{offset_limit}')
        # cmd <<= nm.writelist(header=True, o=nysol_result)

        # 結果はPreviewに入れて返す
        from kskp.store import Preview
        preview = Preview(None, 'csv_to_table')
        # preview.set_content(cmd)
        preview.nysol_result = inputs['i']

        return {'o': preview}  

class VisualizersBokehPlot(VisualizersCommand):
    """
    Bokehを使うとき用
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        p = self.plot(args, inputs)
        script1, div1  = components(p)

        from kskp.store import BokehPlotPreview
        preview = BokehPlotPreview(None, self.__class__.__name__)

        # とりあえず動くようにするため
        preview.data = nm.runfunc(lambda : None) 

        preview.script = script1
        preview.div = div1

        return {'o': preview} 


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



# グラフ化に必要なものの準備
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import holoviews as hv
import random

from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html,components
from bokeh.palettes import Dark2_5 as palette
from bokeh.layouts import gridplot, column
from bokeh.models import HoverTool, Select, Legend, ColumnDataSource
from bokeh.io import output_file, show
from bokeh.models.callbacks import CustomJS
from bokeh.models import Span

from numpy import histogram
import itertools

hv.extension('bokeh')

class CsvToLineGraphCommand2(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        ビジュアライズを描画、保存する。
        """
        # # offset対応
        # offset = int(args.get('offset')) if args.get('offset') else 0
        # limit = int(args.get('limit')) if args.get('limit') else 999999
        # offset_limit = offset + limit
       
        # # inputs['i']にはNysolPythonコマンドが来る
        # nysol_result = []
        # cmd = inputs['i']
        # cmd <<= nm.msel(c=f'{offset}<=line() && line()<{offset_limit}')
        # cmd <<= nm.writelist(header=True, o=nysol_result)
        # cmd.run(msg='on')

        nysol_result = inputs['i']

        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(nysol_result[1:], columns=nysol_result[0])

        # dfの作成
        # TODO:愚直にdfを加工しており、高速化・メモリ管理等の工夫は何もしていない
        time_series_column = args.get('time_series_column') if args.get('time_series_column') else False
        # df = pd.read_csv(file_path, parse_dates=[time_series_column], nrows=limit, skiprows=range(1, offset))
        # df = frame.get_dataframe(limit, offset, [time_series_column])
        df[args.get('data_column')] = df[args.get('data_column')].astype(str)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass
        hv.extension('bokeh')

        keys = args.get('data_column')

        if len(keys) > 0:
            results = self.direct_product_by_keys(df, keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        line_list = {}
        for label, df in named_dfs.items():
            line_list[label] = hv.Curve(df, args.get('time_series_column'), args.get('y_axis_column')).opts(width=1040, height=600)

        ndoverlay = hv.NdOverlay(line_list).opts(legend_position='top',
                                                 width=int(args.get('x_size')), height=int(args.get('y_size')),
                                                 xlabel=args.get('x_label'), ylabel=args.get('y_label'))

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state

        return plot

class CsvToHistogramCommand2(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotのヒストグラムを作成する
        """
        # # offset対応
        # offset = int(args.get('offset')) if args.get('offset') else 0
        # limit = int(args.get('limit')) if args.get('limit') else 999999
        # offset_limit = offset + limit

        # # inputs['i']にはNysolPythonコマンドが来る
        # nysol_result = []
        # cmd = inputs['i']
        # cmd <<= nm.msel(c=f'{offset}<=line() && line()<{offset_limit}')
        # cmd <<= nm.writelist(header=True, o=nysol_result)
        # cmd.run(msg='on')

        nysol_result = inputs['i']

        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(nysol_result[1:], columns=nysol_result[0])

        # frame = Library.load_frame(inputs.get('i'))
        # df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        # df = frame.get_dataframe(limit, offset)
        df[args.get('data_column')] = df[args.get('data_column')].astype(str)
        df[args.get('x_axis')] = df[args.get('x_axis')].astype(int)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        keys = args.get('data_column')

        if len(keys) > 0:
            results = self.direct_product_by_keys(df, keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        hist_list = {}
        for label, df in named_dfs.items():
            hist, edges = np.histogram(df[args.get('x_axis')].tolist(), bins=args.get('bins'))
            hist_list[label] = hv.Histogram((edges, hist)).opts(muted_alpha=0.1)

        ndoverlay = hv.NdOverlay(hist_list).opts(legend_position='top',
                                                 width=int(args.get('x_size')), height=int(args.get('y_size')),
                                                 xlabel=args.get('x_label'), ylabel=args.get('y_label'))

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state

        return plot

class CsvToScatterCommand2(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの散布図を作成する
        """
        # # offset対応
        # offset = int(args.get('offset')) if args.get('offset') else 0
        # limit = int(args.get('limit')) if args.get('limit') else 999999
        # offset_limit = offset + limit

        # # inputs['i']にはNysolPythonコマンドが来る
        # nysol_result = []
        # cmd = inputs['i']
        # cmd <<= nm.msel(c=f'{offset}<=line() && line()<{offset_limit}')
        # cmd <<= nm.writelist(header=True, o=nysol_result)
        # cmd.run(msg='on')

        nysol_result = inputs['i']

        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(nysol_result[1:], columns=nysol_result[0])

        # frame = Library.load_frame(inputs.get('i'))
        # df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        # df = frame.get_dataframe(limit, offset)

        # ブロック句
        # if not frame.file_exists:
        #     return ''

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        df[args.get('x_axis')] = df[args.get('x_axis')].astype(int)
        df[args.get('y_axis')] = df[args.get('y_axis')].astype(int)

        keys = args.get('data_column')

        if len(keys) > 0:
            results = self.direct_product_by_keys(df, keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        scatter_list = {}
        for label, _df in named_dfs.items():
            scatter_list[label] = hv.Scatter(_df, args.get('x_axis'), vdims=[args.get('y_axis')]).opts(muted_alpha=0.1)

        ndoverlay = hv.NdOverlay(scatter_list).opts(legend_position='top',
                                                 width=int(args.get('x_size')), height=int(args.get('y_size')),
                                                 xlabel=args.get('x_label'), ylabel=args.get('y_label'))
        if not args.get('b'):
            b = hv.Bivariate(df[[args.get('x_axis'), args.get('y_axis')]]).opts(show_legend=False, bandwidth=0.5, axiswise=True, line_width=2, colorbar=True)
            ndoverlay = ndoverlay * b

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state

        return plot

class CsvToBoxplotCommand2(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()
        
    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの箱ひげ図を作成する
        """
        # # offset対応
        # offset = int(args.get('offset')) if args.get('offset') else 0
        # limit = int(args.get('limit')) if args.get('limit') else 999999
        # offset_limit = offset + limit

        # # inputs['i']にはNysolPythonコマンドが来る
        # nysol_result = []
        # cmd = inputs['i']
        # cmd <<= nm.msel(c=f'{offset}<=line() && line()<{offset_limit}')
        # cmd <<= nm.writelist(header=True, o=nysol_result)
        # cmd.run(msg='on')

        nysol_result = inputs['i']

        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(nysol_result[1:], columns=nysol_result[0])

        # frame = Library.load_frame(inputs.get('i'))
        # df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        # df = frame.get_dataframe(limit, offset)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # passd

        df[args.get('x_axis')] = df[args.get('x_axis')].astype(float)
        df[args.get('y_axis')] = df[args.get('y_axis')].astype(float)

        hv.extension('bokeh')
        x_label = args.get('x_label') if args.get('x_label') else ','.join(args.get('x_axis'))
        y_label = args.get('y_label') if args.get('y_label') else args.get('y_axis')
        title = args.get('graph_title')

        boxwhisker = hv.BoxWhisker(df, kdims=args.get('x_axis'), vdims=args.get('y_axis'), label=title)
        boxwhisker.opts(width=args.get('x_size'), height=args.get('y_size'), xlabel=x_label, ylabel=y_label)

        renderer = hv.renderer('bokeh')
        plot=renderer.get_plot(boxwhisker).state

        return plot

class CsvtoRepetitivieWaveform2(VisualizersBokehPlot):

    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの反復波形図を作成する
        """
        self.init(args, inputs)
        
        graph_source = self.get_graph_source(self.df, disableTooltips=self.disableTooltips) 
        graph_colors = self.get_colors(len(graph_source))
        graph_plot = self.get_plot("反復波形図")
        graph_plot = self.get_grpah_plot(graph_plot,graph_source, graph_colors)
        graph_plot.legend.location = "top_left"
        graph_plot.legend.click_policy = "mute"

        select = self.get_select(graph_plot)
        plots = [graph_plot, select]
        
        statics_plot = None
        if self.disableStatics == False:
            statics_source = self.get_statics_source(self.df, disableTooltips=self.disableTooltips)
            if statics_source is not None:
                statics_colors = self.get_colors(len(statics_source))
                plot = self.get_plot("反復波形図",graph_plot.x_range,graph_plot.y_range)
                statics_plot = self.get_statics_plot(plot,statics_source, statics_colors)
                if statics_plot.legend:
                    statics_plot.legend.location = "top_left"
                    statics_plot.legend.click_policy = "mute"
                plots.append(statics_plot)          
        
        return gridplot(plots, ncols=1, plot_width=self.graph_width, plot_height=self.graph_height)
        
      
    def init(self, args, inputs):
    
        # # データ表示範囲の設定
        # offset = int(args.get('offset')) if args.get('offset') else 0
        # limit = int(args.get('limit')) if args.get('limit') else 999999
        # offset_limit = offset + limit

        # # inputs['i']にはNysolPythonコマンドが来る
        # nysol_result = []
        # cmd = inputs['i']
        # cmd <<= nm.msel(c=f'{offset}<=line() && line()<{offset_limit}')
        # cmd <<= nm.writelist(header=True, o=nysol_result)
        # cmd.run(msg='on')

        nysol_result = inputs['i']
        
        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(nysol_result[1:], columns=nysol_result[0])

        # 共通パラメーター
        # frame_uuid = inputs.get('i')
        # 軸の設定
        self.column_name_x_axis = args.get('x_axis')[0]['column']
        self.column_name_values = args.get('y_axis')[0]['column']
        self.x_axis_label = args.get('x_axis')[0]['label']
        self.y_axis_label = args.get('y_axis')[0]['label']

        # データ系列の設定
        self.keys = args.get('datas') if args.get('datas') else None
        self.group = args.get('group')

        # データ表示範囲の設定
        # offset = int(args.get('offset')) if args.get('offset') else 0
        # limit = int(args.get('limit')) if args.get('limit') else None
        
        # frame = Library.load_frame(frame_uuid)
        # df = frame.get_dataframe(limit, offset)
        self.df = df.sort_values(by = self.column_name_x_axis)
        self.groups = self.df[self.group].unique().tolist()
        
        # グラフ表示要素の設定
        self.disableTooltips = args.get('disableTooltips') if args.get('disableTooltips') else False
        self.disableMarker = args.get('disableMarker') if args.get('disableMarker') else False
        self.disableStatics = args.get('disableStatics') if args.get('disableStatics') else False
        self.disableEvent = args.get('disableEvent') if args.get('disableEvent') else False
        self.event = args.get('event')
        self.statics = args.get('statics')
        
        # グラフサイズの設定
        self.graph_width = args.get('width')
        self.graph_height = height=args.get('height')
        
        #共通設定
        self.tools = "pan,wheel_zoom,box_zoom,reset,save,box_select"
        self.tooltips = None

    def get_graph_source(self, df, disableTooltips=False):

        named_dfs = {}
        if self.keys is not None and len(self.keys) > 0:
            results = self.direct_product_by_keys(df, self.keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs['all'] = df
  
        ## source
        source = {}
        for label, n_df in named_dfs.items():
            data = dict(
                x = n_df[self.column_name_x_axis].tolist(),
                y = n_df[self.column_name_values].tolist(),
                #group = n_df[self.group].tolist(),
                label = [label] * (len(n_df.index))
            )
            source[label] = data
        
        return source

    def get_statics_source(self, df, disableTooltips=False):
        k = self.column_name_x_axis
        f = self.column_name_values
        c = self.statics #"min,mean,max,qtile1,median,qtile3"
        i = self.df.values.tolist()
        i.insert(0,list(df.columns))

        dtype = "{}:float".format(self.column_name_x_axis)
        result = None
        result <<= nm.msummary(i=i, k=k, f=f, c=c).writelist(dtype=dtype, header=True)
        result = result.run()

        name=result.pop(0)
        df= pd.DataFrame(result,columns=name)
        df = df.sort_values(by = self.column_name_x_axis)
        keys = c.split(',')
        source = {}
        x = df[k].tolist()
        for key in keys:
            data = dict(
                x = x,
                y = df[key].tolist(),
                label = [key] * (len(x))
            )
            source[key] = data

        return source

    def get_select(self, plot):
        values = self.groups
        values.insert(0, '')

        s = Select(value=values[0], title=self.group, options=values, width=120)

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

    def get_colors(self, size):
        i = 0
        colors = []
        for d in itertools.cycle(palette):
            if i >= size:
                break
            colors.append(d)
            i = i + 1

        return colors

    def get_plot(self, title, x_range=None, y_range=None):
        
        tooltips = None
        if self.disableTooltips != True:
            tooltips = [
                    ("凡例", "@label"),
                    (self.column_name_x_axis, "@x"),
                    (self.column_name_values, "@y"),
                ]
        
        plot = figure(
            title=title,
            tools=self.tools,
            tooltips=tooltips,
            x_axis_label=self.x_axis_label,
            y_axis_label=self.y_axis_label
        )
        if x_range is not None:
            plot.x_range = x_range
        if y_range is not None:
            plot.y_range = y_range

        return plot

    def add_lines_to_plot(self, figure_plot, source, colors):
        for label, color in zip(source,colors):
            figure_plot.line('x', 'y', source=source[label], legend=label, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2)
        
        return figure_plot

    def add_points_to_plot(self, figure_plot, source, colors):
        for label, color in zip(source,colors):
            figure_plot.circle('x', 'y', source=ColumnDataSource(data=source[label]), legend=label, color=color, alpha=0.9, muted_color=color, muted_alpha=0.2, size=8)
        
        return figure_plot

    def add_varea_to_plot(self, figure_plot, source, fill_color='#cccccc'):
        keys = self.statics.split(',')
        length = len(keys)
        for index, key in enumerate(keys):
            if (index + 1) < length:
                x = source[key]['x']
                y1 = source[key]['y']
                y2 = source[keys[index + 1]]['y']
                figure_plot.varea(x=x, y1=y1, y2=y2, fill_color=fill_color, alpha=0.5)

        return figure_plot

    def add_span_to_plot(self, figure_plot, df):
        queryStr = "{0} == {1}".format(self.event, "0")
        result_df = df.query(queryStr)

        from bokeh.models import Span

        xs = result_df[self.column_name_x_axis].unique().tolist()

        for x in xs:
            s = Span(location= x,
                              dimension='height', line_color='black',
                              line_dash='dashed', line_width=3, line_alpha=0.3)
            figure_plot.add_layout(s)

        return figure_plot

    def get_statics_plot(self, plot, source, colors):        
        # plot
        if source == None:
            return plot

        plot = self.add_lines_to_plot(plot, source, colors)
        plot = self.add_varea_to_plot(plot, source)
        if self.disableEvent != True:
            plot = self.add_span_to_plot(plot, self.df)
        if self.disableMarker != True:
            plot = self.add_points_to_plot(plot, source, colors)
       
        return plot 

    def get_grpah_plot(self, plot, source, colors):

        # plot
        if source == None:
            return plot
        plot = self.add_lines_to_plot(plot, source, colors)
        if self.disableEvent != True:
            plot = self.add_span_to_plot(plot, self.df)
        if self.disableMarker != True:
            plot = self.add_points_to_plot(plot, source, colors)

        return plot
