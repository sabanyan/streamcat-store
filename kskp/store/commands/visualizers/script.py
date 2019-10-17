# ビジュアライズコマンド
import os

from kskp.core import Command, Port
from kskp.store import Library

import nysol.mcmd as nm
import pprint
pp = pprint.PrettyPrinter(indent=4)


class VisualizersCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'table')]

    def run(self, args, inputs):
        # HTML作成
        visualize_html = self.template_data(args, inputs)
        return { 'o': visualize_html }

    def template_data(self, args, inputs):
        """ for override """
        raise Exception()

class VisualizersHtml(VisualizersCommand):
    """
    Bokehを使うコマンドと分けたかったのでとりあえず作成
    とりあえず感が半端ない。。。
    """
    def __init__(self):
        super().__init__()

class VisualizersBokehPlot(VisualizersCommand):
    """
    Bokehを使うとき用
    """
    def __init__(self):
        super().__init__()

    def template_data(self, args, inputs):
        """
        csvのファイルパスから、
        plotの折れ線グラフ画像のimageタグを作成する
        """
        p = self.plot(args, inputs)

        result = {}

        script1, div1  = components(p)

        result['script'] = script1
        result['div'] = div1

        return result

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


class CsvToTableCommand(VisualizersHtml):
    def __init__(self):
        super().__init__()

    def template_data(self, args, inputs):
        """
        csvのファイルパスから、
        HTMLのテーブル形式にして返す
        """
        # inputsにはuuidが来る
        frame = Library.load_frame(inputs.get('i'))
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        # ブロック句
        if not frame.file_exists:
            return ''

        # テーブル構造
        return frame.get_table(limit, offset)

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
from numpy import histogram
import itertools

hv.extension('bokeh')

class CsvToLineGraphCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        ビジュアライズを描画、保存する。
        """
        # offset対応
        frame = Library.load_frame(inputs.get('i'))
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        # dfの作成
        # TODO:愚直にdfを加工しており、高速化・メモリ管理等の工夫は何もしていない
        time_series_column = args.get('time_series_column') if args.get('time_series_column') else False
        # df = pd.read_csv(file_path, parse_dates=[time_series_column], nrows=limit, skiprows=range(1, offset))
        df = frame.get_dataframe(limit, offset, [time_series_column])
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

class CsvToHistogramCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotのヒストグラムを作成する
        """

        # offset対応
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        frame = Library.load_frame(inputs.get('i'))
        # df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        df = frame.get_dataframe(limit, offset)
        df[args.get('data_column')] = df[args.get('data_column')].astype(str)

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

class CsvToScatterCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの散布図を作成する
        """
        # offset対応
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        frame = Library.load_frame(inputs.get('i'))
        # df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        df = frame.get_dataframe(limit, offset)

        # ブロック句
        if not frame.file_exists:
            return ''

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

class CsvToBoxplotCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの箱ひげ図を作成する
        """
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        frame = Library.load_frame(inputs.get('i'))
        # df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        df = frame.get_dataframe(limit, offset)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # passd

        hv.extension('bokeh')
        x_label = args.get('x_label') if args.get('x_label') else ','.join(args.get('x_axis'))
        y_label = args.get('y_label') if args.get('y_label') else args.get('y_axis')
        title = args.get('graph_title')

        boxwhisker = hv.BoxWhisker(df, kdims=args.get('x_axis'), vdims=args.get('y_axis'), label=title)
        boxwhisker.opts(width=args.get('x_size'), height=args.get('y_size'), xlabel=x_label, ylabel=y_label)

        renderer = hv.renderer('bokeh')
        plot=renderer.get_plot(boxwhisker).state

        return plot

class CsvtoRepetitivieWaveform(VisualizersBokehPlot):

    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの反復波形図を作成する
        """
        self.init(args, inputs)

        ## source
        sources = {}
        for label, df in self.named_dfs.items():
            data = dict(
                x = df[self.column_name_x_axis].tolist(),
                y = df[self.column_name_values].tolist(),
                group = df[self.group].tolist(),
                label = [label] * (len(df.index))
            )
            sources[label] = data

        plot = self.get_grpah_plot("反復波形図",sources)

        return plot

    def init(self, args, inputs):
    
        # 共通パラメーター
        frame_uuid = inputs.get('i')

        # 軸の設定
        self.column_name_x_axis = args.get('x_axis')[0]['column']
        self.column_name_values = args.get('y_axis')[0]['column']
        self.x_axis_label = args.get('x_axis')[0]['label']
        self.y_axis_label = args.get('y_axis')[0]['label']

        # データ系列の設定
        self.keys = args.get('datas')
        self.group = args.get('group')

        # データ表示範囲の設定
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None
        
        frame = Library.load_frame(frame_uuid)
        df = frame.get_dataframe(limit, offset)

        named_dfs = {}
        if self.keys is not None and len(self.keys) > 0:
            results = self.direct_product_by_keys(df, self.keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs['all'] = df
        self.groups = df[self.group].unique().tolist()
        self.named_dfs = named_dfs
        
        # グラフ表示要素の設定
        self.disableTooltips = args.get('doTooltips')
        self.disableMarker = args.get('doMarker')
        self.disableStatics = args.get('doStatics')
        self.disableEvent = args.get('doEvent')
        self.event = args.get('event')
        self.statics = args.get('statics')
        
        # グラフサイズの設定
        self.graph_width = args.get('width')
        self.graph_height = height=args.get('height')
        
        #共通設定
        self.tools = "pan,wheel_zoom,box_zoom,reset,save,box_select"
        self.tooltips = []

        # ツールチップを表示
        if self.disableTooltips :
            self.tooltips = [
                ('', "@label"),
                (self.group, "@group"),
                (self.column_name_x_axis, "@x"),
                (self.column_name_values, "@y"),
            ]

    def get_statics_plot(self, title, sources):
        plot = figure(title=title, tools=self.tools,tooltips=self.tooltips)

        args = {
            'k':self.column_name_x_axis,
            'f':self.column_name_values,
            'c':args.get('statics')
        }
        statics = {}
        #for label, df in sources:


        return plot 

    def get_grpah_plot(self, title, sources):
        f = figure(title=title, tools=self.tools, tooltips=self.tooltips, width=self.graph_width, height=self.graph_height,x_axis_label=self.x_axis_label, y_axis_label=self.y_axis_label)
        
        elements = {}
        colors = itertools.cycle(palette)
        for label, color in zip(sources,colors):
            elements[label] = []
            elements[label].append(f.line('x', 'y', source=sources[label], legend=label, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2))
             # マーカーを表示
            if self.disableMarker != True:
                elements[label].append(f.circle('x', 'y', source=sources[label], legend=label, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2))
            
        f.legend.location = "top_left"
        f.legend.click_policy = "mute"

        attrs = sorted(self.groups)
        attrs.insert(0, '-All-')
        attr_select = Select(value=attrs[0], title=self.group, options=attrs) 
        
        callback = CustomJS(args=dict(sources=sources, elements=elements, select=attr_select, attrs_list=attrs, name_attrs=self.group), code="""
                
            var isMute = (id, attr, filtered) => {
                return !(attr === filtered['selected_attr'])
            }
            var update = (key, mute) => { 
                elements[key].map((graphElement) => {
                    graphElement.muted = mute
                })
            }

            var clear = (key) => { 
                elements[key].map((graphElement) => {
                    graphElement.muted = false
                })
            }

            var value = select.value
            var filtered = {'selected_attr':value}
            for (key in sources) {
                var source_id = key
                var source_attr = sources[key][name_attrs]
                var mute = isMute(key, source_attr, filtered)
                if (value === attrs_list[0]) {
                    clear(key)
                } else {
                    update(key, mute)
                }
            }
        """)

        attr_select.js_on_change('value', callback)

        return gridplot([f, attr_select], ncols=1)
