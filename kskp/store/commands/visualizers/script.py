# ビジュアライズコマンド
import os

from kskp.core import Command, Port

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

    def generate_random_color(self):
        """
        ランダムに色を出力
        bokehは色を指定しないといけないので（デフォルトだと全て同じ色になってしまう）
        """
        return '#{:X}{:X}{:X}'.format(*[random.randint(0, 255) for _ in range(3)])

    def color_gen(self):
        from bokeh.palettes import Category10
        import itertools
        yield from itertools.cycle(Category10[10])

class CsvToTableCommand(VisualizersHtml):
    def __init__(self):
        super().__init__()

    def template_data(self, args, inputs):
        """
        csvのファイルパスから、
        HTMLのテーブル形式にして返す
        """
        from kskp.store import Library
        # inputsにはパスが来て欲しい
        file_path = Library.load_frame(inputs.get('i')).path
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        # ブロック句
        if not os.path.exists(file_path):
            return ''

        result = {}

        # テーブル構造
        with open(file_path, 'r', errors = 'ignore') as f:
            n = 0

            result['reader'] = []
            for line in f:
                # 指定されたlimitの数だけ要素が達していたら終了
                if limit is not None and len(result['reader']) == limit:
                    break

                if n == 0:
                    # 一行目はヘッダとみなす
                    result['header'] = line.split(',')
                else:
                    if offset < n:
                        result['reader'].append(line.split(','))

                n += 1

        return result

# グラフ化に必要なものの準備
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import holoviews as hv
import random

from bokeh.plotting import figure, ColumnDataSource
from bokeh.resources import CDN
from bokeh.embed import file_html,components
from bokeh.models import HoverTool
from bokeh.io import output_file, show
from numpy import histogram

class CsvToLineGraphCommand(VisualizersBokehPlot):
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        ビジュアライズを描画、保存する。
        """

        # offset対応
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        # dfの作成
        # index_colで指定しているものがx軸になる
        time_series_column = args.get('time_series_column') if args.get('time_series_column') else False
        df = pd.read_csv(inputs.get('i'), parse_dates=time_series_column, nrows=limit, skiprows=range(1, offset))
        df[args.get('data_column')] = df[args.get('data_column')].astype(str)

        # start = offset
        # end = start + (limit if limit is not None else len(df))

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        df = df.sort_values(args.get('x_axis_column'))

        # 時系列表示設定
        tooltip = '@' + args.get('x_axis_column')
        tooltip_format = 'numeral'
        type = 'auto'
        if time_series_column:
            # そのままHTMLに出力されるので{%F}だけだと、jinja2が勘違いをする
            # それを防ぐために{%raw%}{%endraw%}で区切っている
            tooltip = '@' + args.get('x_axis_column') + '{%F}'
            tooltip_format = 'datetime'
            type = 'datetime'

        # tooltipの設定
        hover = HoverTool()

        hover.tooltips = [
            (args.get('x_axis_column'), tooltip),
            (args.get('y_axis_column'), '@' + args.get('y_axis_column'))
        ]
        hover.formatters = {
            args.get('x_axis_column'): tooltip_format
        }
        hover.mode='vline'

        plot = figure(x_axis_type=type,
                      x_axis_label=args.get('x_label'),
                      y_axis_label=args.get('y_label'),
                      output_backend="webgl",
                      title=args.get('graph_title'),
                      plot_width=args.get('x_size'),
                      plot_height=args.get('y_size'))

        color = self.color_gen()
        unique_data = df[args.get('data_column')].unique().tolist()

        # クエリ
        # if len(args.get('data')) > 0:
        #     unique_data = args.get('data')

        # データ名が入っている列が存在する場合（縦持ち）
        for datum in unique_data:
            source = ColumnDataSource(df[df[args.get('data_column')]==datum])
            plot.line(x=args.get('x_axis_column'), y=args.get('y_axis_column'),
                      legend=datum, alpha=args.get('alpha'), color=color.__next__(),
                      source=source)

        # データが列ごとに分かれている場合（横持ち）
        # for datum in args.get('data'):
        #     source = ColumnDataSource(data={
        #         args.get('x_axis_column'): df[args.get('x_axis_column')],
        #         args.get('y_axis_column'): df[datum.get('name')]
        #     })
        #     plot.line(x=args.get('x_axis_column'), y=args.get('y_axis_column'), legend=datum.get('legend_name'),
        #               color=datum.get('color'), source=source)

        # plot.add_tools(hover)
        plot.legend.location = "top_right"
        plot.legend.click_policy="hide"

        # html = file_html(plot, CDN, 'myplot')

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

        file_path = inputs.get('i')
        df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        df[args.get('data_column')] = df[args.get('data_column')].astype(str)

        # start = offset
        # end = start + (limit if limit is not None else len(df))

        # ブロック句
        # if not os.path.exists(file_path):
        #     return ''

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        hover = HoverTool()
        hover.tooltips = [
            ('度数', '@top')
        ]
        hover.mode='vline'

        plot = figure(plot_width=args.get('x_size'),
                      plot_height=args.get('y_size'),
                      x_axis_label=args.get('x_label'),
                      y_axis_label=args.get('y_label'),
                      output_backend="webgl",
                      title=args.get('graph_title'))

        color = self.color_gen()
        unique_data = df[args.get('data_column')].unique().tolist()

        # if len(args.get('data')) > 0:
        #     unique_data = args.get('data')

        for datum in unique_data:
            hist, edges = histogram(df[df[args.get('data_column')]==datum][args.get('x_axis')].tolist(),
                                    bins=args.get('bins'), density=args.get('density'))
            source = ColumnDataSource({'top':hist, 'left': edges[:-1], 'right': edges[1:]})
            plot.quad(top='top', bottom=0, left='left', right='right',
                      fill_alpha=args.get('alpha'), color=color.__next__(), legend=datum,
                      source=source)

        plot.add_tools(hover)
        plot.legend.location = "top_right"
        plot.legend.click_policy="hide"

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

        file_path = inputs.get('i')
        df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))
        # df[args.get('data_column')] = df[args.get('data_column')].astype(str)
        #
        # start = offset
        # end = start + (limit if limit is not None else len(df))

        # ブロック句
        if not os.path.exists(file_path):
            return ''

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        # y軸の設定はここ
        # y軸はリスト型。インデックスでも列名でも大丈夫。
        # csvで同名の列名があることがあるので、基本インデックスでいい気がする

        hover = HoverTool()
        hover.tooltips = [
            (args.get('x_axis'), '@x'),
            (args.get('y_axis'), '@y')
        ]

        plot = figure(plot_width=args.get('x_size'),
                      plot_height=args.get('y_size'),
                      x_axis_label=args.get('x_label') if args.get('x_label') is not None else args.get('x_axis'),
                      y_axis_label=args.get('y_label') if args.get('y_label') is not None else args.get('y_axis'),
                      output_backend="webgl",
                      title=args.get('graph_title'))

        color = self.color_gen()
        # unique_data = df[args.get('data_column')].unique().tolist()

        # if len(args.get('data')) > 0:
        #     unique_data = args.get('data')

        # for datum in unique_data:
        df_select_datum = df
        source = ColumnDataSource({'x': df_select_datum[args.get('x_axis')], 'y': df_select_datum[args.get('y_axis')]})
        plot.scatter(x='x', y='y', fill_alpha=args.get('alpha'),
                     color=color.__next__(), alpha=args.get('alpha'),
                     source=source)

        plot.add_tools(hover)
        plot.legend.location = "top_right"
        plot.legend.click_policy="hide"

        return plot

class CsvToBoxplotCommand(VisualizersBokehPlot):
    """
    厳密にはbokehを直接は使っていない
    holoviewsというbokehやmatplotlibをラップしたライブラリを使用している
    bokehをラップしているので、bokehのメソッドを使える。
    なので、VisualizersBokehPlotをオーバーライドしている
    """
    def __init__(self):
        super().__init__()

    def plot(self, args, inputs):
        """
        csvのファイルパスから、
        plotの箱ひげ図を作成する
        """

        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        file_path = inputs.get('i')
        df = pd.read_csv(file_path, nrows=limit, skiprows=range(1, offset))

        # ブロック句
        # if not os.path.exists(file_path):
        #     return ''

        # ここstartがdfの最大行数を越えるとエラーが出る
        # if len(df) < start:
            # なんかする
            # pass

        # ここはbokehをラップしているライブラリのholoviewsを使っている
        # bokehは書き方がめんどくさいため
        hv.extension('bokeh')
        x_label = args.get('x_label') if args.get('x_label') else ','.join(args.get('x_axis'))
        y_label = args.get('y_label') if args.get('y_label') else args.get('y_axis')
        title = args.get('graph_title')

        boxwhisker = hv.BoxWhisker(df, kdims=args.get('x_axis'), vdims=args.get('y_axis'), label=title)
        boxwhisker.opts(width=args.get('x_size'), height=args.get('y_size'), xlabel=x_label, ylabel=y_label)

        renderer = hv.renderer('bokeh')
        plot=renderer.get_plot(boxwhisker).state

        return plot
