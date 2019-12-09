# ビジュアライズコマンド
import os
from kskp.core import Command, Port

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
        # 結果はVisに入れて返す
        from kskp.store import Vis
        column_names = inputs['i'][0] if len(inputs['i']) > 0 else []
        matrix = inputs['i'][1:] if len(inputs['i']) > 1 else [[]]
        vis = Vis(None, 'csv_to_table', column_names, matrix)

        return {'o': vis}  

class VisualizersBokehPlot(VisualizersCommand):
    """
    Bokehを使うとき用
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        column_names = inputs['i'][0] if len(inputs['i']) > 0 else []
        matrix = inputs['i'][1:] if len(inputs['i']) > 1 else [[]]
        p = self.plot(args, column_names, matrix)
        script1, div1 = components(p)

        from kskp.store import BokehPlotVis
        label = self.__class__.__name__
        vis = BokehPlotVis(None, label, column_names, script1, div1)

        # とりあえず動くようにするため
        # vis.data = nm.runfunc(lambda : None)

        return {'o': vis} 

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

from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html,components
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

    def plot(self, args, column_names, matrix):
        """
        ビジュアライズを描画、保存する。
        """
        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(matrix, columns=column_names)

        # dfの作成
        data_columns = args.get('data_column') or self._infer_data_columns(column_names)
        df[data_columns] = df[data_columns].astype(str)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass
        hv.extension('bokeh')

        keys = data_columns

        if len(keys) > 0:
            results = self.direct_product_by_keys(df, keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        line_list = {}
        for label, df in named_dfs.items():
            time_series_column = args.get('time_series_column') or self._infer_time_series_column(column_names)
            y_axis_column = args.get('y_axis_column') or self._infer_y_axis_column(column_names)
            line_list[label] = hv.Curve(df, time_series_column, y_axis_column).opts(width=1040, height=600)

        x_size = args.get('x_size') or self._proper_x_size()
        y_size = args.get('y_size') or self._proper_y_size()
        ndoverlay = hv.NdOverlay(line_list).opts(legend_position='top',
                                                 width=x_size, height=y_size,
                                                 xlabel=args.get('x_label'), ylabel=args.get('y_label'))

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state

        return plot

class CsvToHistogramCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, column_names, matrix):
        """
        ListデータをVisデータにして返す
        """
        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(matrix, columns=column_names)

        # dfの作成
        data_columns = args.get('data_column') or self._infer_data_columns(column_names)
        x_axis = args.get('x_axis') or self._infer_x_axis_column(column_names)
        df[data_columns] = df[data_columns].astype(str)
        df[x_axis] = df[x_axis].astype(int)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        keys = data_columns

        if len(keys) > 0:
            results = self.direct_product_by_keys(df, keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        hist_list = {}
        for label, df in named_dfs.items():
            bins = args.get('bins') or self._infer_bins_columns(column_names)
            hist, edges = np.histogram(df[x_axis].tolist(), bins=bins)
            hist_list[label] = hv.Histogram((edges, hist)).opts(muted_alpha=0.1)

        x_size = args.get('x_size') or self._proper_x_size()
        y_size = args.get('y_size') or self._proper_y_size()
        ndoverlay = hv.NdOverlay(hist_list).opts(legend_position='top',
                                                 width=x_size, height=y_size,
                                                 xlabel=args.get('x_label'), ylabel=args.get('y_label'))

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state

        return plot

    def _infer_bins_columns(self, column_names):
        """
        Binsになりそうなデータ列を取得する
        """
        return [self._get_proper_column(column_names, 4)]

class CsvToScatterCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, column_names, matrix):
        """
        ListデータをVisデータにして返す
        """
        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(matrix, columns=column_names)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        # dfの作成
        x_axis = args.get('x_axis') or self._infer_x_axis_column(column_names)
        y_axis = args.get('y_axis') or self._infer_y_axis_column(column_names)
        df[x_axis] = df[x_axis].astype(int)
        df[y_axis] = df[y_axis].astype(int)

        data_columns = args.get('data_column') or self._infer_data_columns(column_names)
        keys = data_columns

        if len(keys) > 0:
            results = self.direct_product_by_keys(df, keys)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        scatter_list = {}
        for label, _df in named_dfs.items():
            scatter_list[label] = hv.Scatter(_df, x_axis, vdims=[y_axis]).opts(muted_alpha=0.1)

        x_size = args.get('x_size') or self._proper_x_size()
        y_size = args.get('y_size') or self._proper_y_size()
        ndoverlay = hv.NdOverlay(scatter_list).opts(legend_position='top',
                                                    width=x_size, height=y_size,
                                                    xlabel=args.get('x_label'), ylabel=args.get('y_label'))
        if not args.get('b'):
            b = hv.Bivariate(df[[x_axis, y_axis]]).opts(show_legend=False, bandwidth=0.5, axiswise=True, line_width=2, colorbar=True)
            ndoverlay = ndoverlay * b

        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(ndoverlay).state

        return plot

class CsvToBoxplotCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()
        
    def plot(self, args, column_names, matrix):
        """
        ListデータをVisデータにして返す
        """
        # NysolPythonの結果をpandasのDataFrameに変換する
        df = pd.DataFrame(matrix, columns=column_names)

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # passd

        # dfの作成
        x_axis = args.get('x_axis') or self._infer_x_axis_column(column_names)
        y_axis = args.get('y_axis') or self._infer_y_axis_column(column_names)
        df[x_axis] = df[x_axis].astype(float)
        df[y_axis] = df[y_axis].astype(float)

        hv.extension('bokeh')
        title = args.get('graph_title') or ''
        x_size = args.get('x_size') or self._proper_x_size()
        y_size = args.get('y_size') or self._proper_y_size()
        x_label = args.get('x_label') if args.get('x_label') else ','.join(x_axis)
        y_label = args.get('y_label') if args.get('y_label') else y_axis
        boxwhisker = hv.BoxWhisker(df, kdims=x_axis, vdims=y_axis, label=title)
        boxwhisker.opts(width=x_size, height=y_size, xlabel=x_label, ylabel=y_label)

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
        df = frame.get_dataframe(limit, offset, [x_axis_column])
        
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