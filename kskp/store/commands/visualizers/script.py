# ビジュアライズコマンド
import os

from kskp.core import Command, Port
from kskp.store import Library

import nysol.mcmd as nm

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
from bokeh.models import Span

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
        offset          = int(args.get('offset'))   if args.get('offset')   else 0
        limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))
        

        # 1. frame_uuidでframeを探す。
        frame = Library.load_frame(inputs.get('i'))

        # 2. pandasnのdataframe作成
        # TODO:愚直にdfを加工しており、高速化・メモリ管理等の工夫は何もしていない
        df = frame.get_dataframe(limit, offset)
        df[data_column] = df[data_column].astype(str)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass
        hv.extension('bokeh')

        if len(data_column) > 0:
            results = self.direct_product_by_keys(df, data_column)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        # 3. 折れ線の作成
        line_list = {}
        for label, df in named_dfs.items():
            line_list[label] = hv.Curve(df, x_axis_column, y_axis_column).opts(width=1040, height=600)

        ndoverlay = hv.NdOverlay(line_list).opts(legend_position='top',
                                                 width=graph_width, height=graph_height,
                                                 xlabel=x_axis_label, ylabel=y_axis_label)

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

        # 軸の設定
        x_axis          = args.get('x_axis')
        x_axis_column   = x_axis[0]['column']
        x_axis_label    = x_axis[0]['label']

        # 縦軸列：頻度
        y_axis_label    = ""

        # データ系列の設定
        data_column     = args.get('data_column')   if args.get('data_column') is not None else []

        # データ表示範囲の設定
        offset          = int(args.get('offset'))   if args.get('offset')   else 0
        limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        bins            = int(args.get('bins'))   if args.get('bins') else None
        
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))
        
        # 1. frame_uuidでframeを探す。
        frame = Library.load_frame(inputs.get('i'))

        # 2. pandasnのdataframe作成
        # TODO:愚直にdfを加工しており、高速化・メモリ管理等の工夫は何もしていない
        df = frame.get_dataframe(limit, offset)
        df[data_column] = df[data_column].astype(str)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass
        hv.extension('bokeh')

        if len(data_column) > 0:
            results = self.direct_product_by_keys(df, data_column)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        # 3. ヒストグラムの作成3
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

class CsvToScatterCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの散布図を作成する
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
        offset          = int(args.get('offset'))   if args.get('offset')   else 0
        limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        withoutContourLine  = args.get('withoutContourLine') if args.get('withoutContourLine') else False
        
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))

        # 1. frame_uuidでframeを探す。
        frame = Library.load_frame(inputs.get('i'))

        # 2. pandasnのdataframe作成
        # TODO:愚直にdfを加工しており、高速化・メモリ管理等の工夫は何もしていない
        df = frame.get_dataframe(limit, offset)
        
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

class CsvToBoxplotCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()
        
    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの箱ひげ図を作成する
        """
        # 縦軸列：観測値
        y_axis          = args.get('y_axis')
        y_axis_column   = y_axis[0]['column']
        y_axis_label    = y_axis[0]['label']

        x_axis_label    = ""

        # データ系列の設定
        data_column     = args.get('data_column')   if args.get('data_column') is not None else []

        # データ表示範囲の設定
        offset          = int(args.get('offset'))   if args.get('offset')   else 0
        limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        bins            = int(args.get('bins'))   if args.get('bins') else None
        
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))

        graph_title     = ""

        # 1. frame_uuidでframeを探す。
        frame = Library.load_frame(inputs.get('i'))

        # 2. pandasnのdataframe作成
        # TODO:愚直にdfを加工しており、高速化・メモリ管理等の工夫は何もしていない
        df = frame.get_dataframe(limit, offset)
        hv.extension('bokeh')

        # 3. 箱ひげ図の作成
        boxwhisker = hv.BoxWhisker(df, kdims=data_column, vdims=y_axis_column, label=graph_title)
        boxwhisker.opts(width=graph_width, height=graph_height, xlabel=x_axis_label, ylabel=y_axis_label)

        renderer = hv.renderer('bokeh')
        plot=renderer.get_plot(boxwhisker).state

        return plot

class CsvToRepetitivieWaveCommand(VisualizersBokehPlot):

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
        plots = [select, graph_plot]
        
        statics_plot = None
        if self.disableStatics == False:
            statics_source = self.get_statics_source(self.df, disableTooltips=self.disableTooltips)
            if statics_source is not None:
                statics_colors = self.get_colors(len(statics_source))
                plot = self.get_plot("反復波形図",graph_plot.x_range,graph_plot.y_range,False)
                statics_plot = self.get_statics_plot(plot,statics_source, statics_colors)
                if statics_plot.legend:
                    statics_plot.legend.location = "top_left"
                    statics_plot.legend.click_policy = "mute"
                plots.append(statics_plot)          
        
        return gridplot(plots, ncols=1, plot_width=self.graph_width, plot_height=self.graph_height)
        
      
    def init(self, args, inputs):
    
        # 共通パラメーター
        frame_uuid = inputs.get('i')
        # 軸の設定
        self.column_name_x_axis = args.get('x_axis')[0]['column']
        self.column_name_values = args.get('y_axis')[0]['column']
        self.x_axis_label = args.get('x_axis')[0]['label']
        self.y_axis_label = args.get('y_axis')[0]['label']

        # データ系列の設定
        self.keys = args.get('datas') if args.get('datas') else None
        self.group = args.get('group')

        # データ表示範囲の設定
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None
        
        frame = Library.load_frame(frame_uuid)
        df = frame.get_dataframe(limit, offset)
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
                group = n_df[self.group].tolist(),
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

    def get_plot(self, title, x_range=None, y_range=None, visiableGroup=True):
        
        tooltips = None
        if self.disableTooltips != True:
            tooltips = [
                    ("凡例", "@label"),
                    (self.column_name_x_axis, "@x"),
                    (self.column_name_values, "@y"),
                    ("group", "@group")
                ]
            if visiableGroup == False:
                tooltips = [
                    ("凡例", "@label"),
                    (self.column_name_x_axis, "@x"),
                    (self.column_name_values, "@y")
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


class CsvToTimeCompressionCommand(VisualizersBokehPlot):

    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):

        # 軸の設定
        x_axis         = args.get('x_axis')
        x_axis_column  = x_axis[0]['column']
        x_axis_label   = x_axis[0]['label']

        y_axis              = args.get('y_axis')
        y_axis_column  = y_axis[0]['column']
        y_axis_label   = y_axis[0]['label']

        # データ系列の設定
        data     = args.get('data')   if args.get('data') is not None else []

        # データ表示範囲の設定
        offset          = int(args.get('offset'))   if args.get('offset')   else 0
        limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        division        = args.get('division')
        statics         = args.get('statics')
        display_pattern = args.get('display_pattern')
        
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))

        # df
        frame_uuid = inputs.get('i')
        frame = Library.load_frame(frame_uuid)
        df = frame.get_dataframe(limit, offset)
        
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

        result = gridplot(plots, ncols=1, plot_width=graph_width, plot_height=graph_height) 
        
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