# ビジュアライズコマンド
import nysol.mcmd as nm
from kskp.core import Command, Port

ErrMsg={
    '1': "VisualizeInitException"
}

class VCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'list'), Port('m', 'list')]
        self.o_ports = [Port('o', 'last')]

    def run(self, args, inputs):
        pass

class CsvToTableCommand(VCommand):
    """
    テーブル表示を出力する
    """
    def run(self, args, inputs):
        """
        ListデータをVisデータにして返す
        """
        from kskp.store import ApparentLast, Vis

        # 直前のRunsCommandがエラーを返した場合、直後のActivityCommandにエラーを渡す
        if inputs['i'].has_exs:
            return {'o': inputs['i']}

        # 入力値としてListDatumを取得する
        list_datum = inputs['i'].datum

        # 結果はVisに入れて返す
        column_names = list_datum[0] if len(list_datum) > 0 else []
        matrix = list_datum[1:] if len(list_datum) > 1 else [[]]
        vis = Vis(None, None, 'csv_to_table', column_names, matrix)
        return {'o': ApparentLast(inputs['i'].out_point, vis)}  

class HoloviewsBaseCommand(VCommand):
    """
    HoloViewsを用いてグラフを出力する
    """
    def __init__(self):
        super().__init__()

        # Bokehを用いてグラフを描画する
        hv.extension('bokeh')
        self.renderer = hv.renderer('bokeh')

    def run(self, args, inputs):
        from bokeh.embed import components
        from kskp.store import ApparentLast, BokehPlotVis

        # 直前のRunsCommandがエラーを返した場合、直後のActivityCommandにエラーを渡す
        if inputs['i'].has_exs:
            return {'o': inputs['i']}

        # 入力値としてListDatumを取得する
        list_datum = inputs['i'].datum
        # ヘッダ行を取得する
        column_names = inputs['m'].datum[0][0:]

        # 先頭行はnm.mcrossが出力した項目名行なので除外する
        # 最終行はnm.mnumberで付加した連番なので除外する
        matrix = list_datum[1:-1] if len(list_datum) > 1 else [[]]

        # データを用意する
        # NOTE: hv.Dataset.sort()を実行するにはnp.array型でなければならない
        matrix_dict = {row[0]:np.array(row[1:]) for row in matrix}

        # プロットする
        plot = self.plot(args, column_names, matrix_dict)

        # HTML要素を取得する
        script, div = components(plot)

        # 結果はVisに入れて返す
        label = self.__class__.__name__
        vis = BokehPlotVis(None, None, label, column_names, script, div)
        return {'o': ApparentLast(inputs['i'].out_point, vis)} 

    def plot(self, args, column_names:list, matrix_dict:dict):
        """
        ビジュアライズを描画、保存する
        """
        pass

    @staticmethod
    def set_common_opts(overlay):
        """
        グラフ共通のオプションを設定する
        """
        # aspect          : グラフ表示域の縦横比率
        # responsive      : グラフ表示域をWebブラウザの表示サイズに合わせる
        # toolbar         : ツールバーの表示位置
        return overlay.opts(aspect=1.5, responsive=True, toolbar='right', framewise=True)

    @staticmethod
    def cast_to_float(vals):
        """
        数値型に型を変換する
        """
        try:
            # 数値に変換できない値はNaN値に変換される
            num_vals = np.genfromtxt(vals, dtype=float, autostrip=True)
            # np.genfromtxt()によって空文字の要素は削除されるので、その場合は変換しない
            if num_vals.size < vals.size:
                return vals
            # NaN値の割合を算出する
            nan_ratio = np.count_nonzero(np.isnan(num_vals)) / num_vals.size
            # NaN値の割合が一定数を超えた場合は変換しない
            if nan_ratio > 0.5:
                return vals
            return num_vals
        except ValueError:
            return vals

    @staticmethod
    def cast_to_datetime(vals):
        """
        日付時刻文字列を自動認識して日付時刻型に変換する
        """
        from dateutil import parser
        try:
            f = np.frompyfunc(parser.parse, nin=1, nout=1)
            return f(vals)
        except:
            return HoloviewsBaseCommand.cast_to_float(vals)

    @staticmethod
    def cast_to_datetime_by_format(vals, format:str):
        """
        指定した書式の文字列から日付時刻型に変換する
        """
        from datetime import datetime
        caster = lambda x: datetime.strptime(x, format)
        try:
            f = np.frompyfunc(caster, nin=1, nout=1)
            return f(vals)
        except:
            return HoloviewsBaseCommand.cast_to_float(vals)

    @staticmethod
    def get_dimension(axis:list):
        if axis is None or not isinstance(axis, list) or len(axis)==0:
            raise Exception(f'axisが指定されていない、またはlist型ではありません ({axis})')
        axis_column = axis[0].get('column')
        if axis_column is None:
            # エラメッセージ'VisualizeInitException'はエラーダイアログを表示しない
            raise Exception(ErrMsg['1'])
        axis_label = axis[0].get('label', '').strip() or axis_column

        # 軸を設定する
        return hv.Dimension(axis_column, label=axis_label)

    def make_plot(self, overlay):
        from numpy.linalg import LinAlgError
        try:
            # グラフをプロットする
            return self.renderer.get_plot(overlay).state
        except LinAlgError:
            # NOTE: singular matrix (特異行列)は、逆行列が計算できないもののこと
            raise Exception('この軸の設定からは等高線を計算できません。等高線を表示しないを設定ください')
        except Exception:
            raise Exception('この軸の設定からはグラフを表示できません')

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

# グラフ化に必要なものの準備
# 
# TODO: これらのImportは、テストスクリプトの実行時に、以下のWarningを出力している
# ImportWarning: can't resolve package from __spec__ or __package__, falling back on __name__ and __path__
# 
import pandas as pd
import numpy as np
import holoviews as hv
from bokeh.plotting import figure
from bokeh.palettes import Dark2_5 as palette
from bokeh.layouts import gridplot
from bokeh.models import Select, ColumnDataSource, Span
import itertools

class CsvToLineGraphCommand(HoloviewsBaseCommand):
    """
    折線推移グラフを出力する
    """
    def plot(self, args, column_names:list, matrix_dict:dict):
        # X軸(時間軸)を取得する
        time_dim = HoloviewsBaseCommand.get_dimension(args.get('x_axis'))
        # Y軸を取得する
        val_dim = HoloviewsBaseCommand.get_dimension(args.get('y_axis'))

        # 時刻値への型変換関数を取得する
        cast_to_datetime = CsvToLineGraphCommand.get_datetime_cast_func(args)

        # データ系列を取得する
        data_columns = args.get('data_column', [])

        # holoviewsに格納するデータを用意する
        key_dimensions = [time_dim,val_dim] + data_columns
        ds = hv.Dataset(matrix_dict, kdims=key_dimensions)
        # 文字列から数値/日付型へ型変換する
        x_expr = hv.dim(time_dim, cast_to_datetime)
        y_expr = hv.dim(val_dim, HoloviewsBaseCommand.cast_to_float)
        ds = ds.transform((time_dim, x_expr), (val_dim, y_expr))
        # 時間軸の列でソートする
        ds = ds.sort([time_dim])

        if len(data_columns) == 0:
            # データ系列の指定がない場合
            curves = ds.to(hv.Curve, time_dim, val_dim)
            scatters = ds.to(hv.Scatter, time_dim, val_dim).opts(size=5, tools=['hover'])
            overlay = curves * scatters
        else:
            # データ系列の指定がある場合
            ds = ds.select(selection_specs=data_columns)
            curves = ds.to(hv.Curve, time_dim, val_dim)
            scatters = ds.to(hv.Scatter, time_dim, val_dim).opts(size=5, tools=['hover'])
            overlay = curves * scatters
            # X/Y軸とデータ系列の列が重複している場合は.overlay()を使用しない
            if not isinstance(overlay, hv.Overlay):
                overlay = overlay.overlay()

        # グラフ固有のオプションを設定する
        # legend_position : データ系列一覧の表示位置
        overlay = overlay.opts(legend_position='top')

        # グラフ共通のオプションを設定する
        overlay =  HoloviewsBaseCommand.set_common_opts(overlay)

        # グラフをプロットする
        return self.make_plot(overlay)

    @staticmethod
    def get_datetime_cast_func(args):
        # 時間軸の書式
        x_axis_format_select = args.get('x_axis_format_select')
        x_axis_format_custom = args.get('x_axis_format_custom')

        # 時間軸の書式を設定する
        if x_axis_format_select == 'nysol':
            cast_to_datetime = lambda x: HoloviewsBaseCommand.cast_to_datetime_by_format(x, '%Y%m%d%H%M%S.%f')
        elif x_axis_format_select == 'custom': 
            cast_to_datetime = lambda x: HoloviewsBaseCommand.cast_to_datetime_by_format(x, x_axis_format_custom)
        else:
            cast_to_datetime = HoloviewsBaseCommand.cast_to_datetime

        return cast_to_datetime

class CsvToHistogramCommand(HoloviewsBaseCommand):
    """
    ヒストグラムを出力する
    """
    def plot(self, args, column_names:list, matrix_dict:dict):
        # X軸を取得する
        x_dim = HoloviewsBaseCommand.get_dimension(args.get('x_axis'))

        # データ系列を取得する
        data_columns = args.get('data_column', [])

        # グラフ表示要素の設定
        bins = int(args.get('bins')) if args.get('bins') else None

        # holoviewsに格納するデータを用意する
        key_dimensions = [x_dim] + data_columns
        ds = hv.Dataset(matrix_dict, kdims=key_dimensions)
        # 文字列から数値型へ型変換する
        x_expr = hv.dim(x_dim, HoloviewsBaseCommand.cast_to_float)
        ds = ds.transform((x_dim, x_expr))

        # TODO: bins引数の指定が無視される
        # https://github.com/holoviz/holoviews/issues/4651
        try:
            overlay = ds.hist(x_dim, groupby=data_columns, bins=bins, adjoin=False, alpha=0.5, muted_alpha=0.1)
        except Exception:
            raise Exception('この軸の設定からはグラフを表示できません')

        if len(data_columns) == 0:
            # データ系列の指定がない場合
            # tools=['hover'] : Hover表示
            overlay = overlay.opts(tools=['hover'])
        else:
            # データ系列の指定がある場合
            # legend_position : データ系列一覧の表示位置
            # (groupby指定がある場合はHoverが表示されない)
            overlay = overlay.opts(legend_position='top')

        # グラフ共通のオプションを設定する
        overlay = HoloviewsBaseCommand.set_common_opts(overlay)

        # グラフをプロットする
        return self.make_plot(overlay)

class CsvToBoxplotCommand(HoloviewsBaseCommand):
    """
    箱ひげ図を出力する
    """
    def plot(self, args, column_names:list, matrix_dict:dict):
        # X軸を取得する
        y_dim = HoloviewsBaseCommand.get_dimension(args.get('y_axis'))

        # データ系列を取得する
        data_columns = args.get('data_column', [])

        # holoviewsに格納するデータを用意する
        key_dimensions = [y_dim] + data_columns
        ds = hv.Dataset(matrix_dict, kdims=key_dimensions)
        # 文字列から数値型へ型変換する
        y_expr = hv.dim(y_dim, HoloviewsBaseCommand.cast_to_float)
        ds = ds.transform((y_dim, y_expr))

        if len(data_columns) == 0:
            # データ系列の指定がない場合
            overlay = ds.to(hv.BoxWhisker, kdims=[], vdims=y_dim)
        else:
            # データ系列の指定がある場合
            overlay = ds.to(hv.BoxWhisker, kdims=data_columns, vdims=y_dim)

        # グラフ固有のオプションを設定する
        # legend_position : データ系列一覧の表示位置
        # tools=['hover'] : Hover表示
        overlay = overlay.opts(legend_position='top', tools=['hover'])

        # グラフ共通のオプションを設定する
        overlay = HoloviewsBaseCommand.set_common_opts(overlay)

        # グラフをプロットする
        return self.make_plot(overlay)

class CsvToScatterCommand(HoloviewsBaseCommand):
    """
    散布図を出力する
    """
    def plot(self, args, column_names:list, matrix_dict:dict):

        # X軸を取得する
        x_dim = HoloviewsBaseCommand.get_dimension(args.get('x_axis'))
        # Y軸を取得する
        y_dim = HoloviewsBaseCommand.get_dimension(args.get('y_axis'))

        # データ系列を取得する
        data_columns = args.get('data_column', [])

        # グラフ表示要素の設定
        withoutContourLine = args.get('withoutContourLine', False)

        # holoviewsに格納するデータを用意する
        key_dimensions = [x_dim,y_dim] + data_columns
        ds = hv.Dataset(matrix_dict, kdims=key_dimensions)
        # 文字列から数値/日付型へ型変換する
        x_expr = hv.dim(x_dim, HoloviewsBaseCommand.cast_to_datetime)
        y_expr = hv.dim(y_dim, HoloviewsBaseCommand.cast_to_datetime)
        ds = ds.transform((x_dim, x_expr), (y_dim, y_expr))

        if len(data_columns) == 0:
            # データ系列の指定がない場合
            overlay = ds.to(hv.Scatter, x_dim, y_dim).opts(size=5, muted_alpha=0.1, tools=['hover'])
        else:
            # データ系列の指定がある場合
            ds = ds.select(selection_specs=data_columns)
            overlay = ds.to(hv.Scatter, x_dim, y_dim).opts(size=5, muted_alpha=0.1, tools=['hover'])
            # X/Y軸とデータ系列の列が重複している場合は.overlay()を使用しない
            if not isinstance(overlay, hv.Overlay):
                overlay = overlay.overlay()

        if not withoutContourLine:
            b = hv.Bivariate(ds).opts(show_legend=False, bandwidth=0.5, axiswise=True, line_width=2, colorbar=False, alpha=0.1)
            overlay = overlay * b

        # グラフ固有のオプションを設定する
        # legend_position : データ系列一覧の表示位置
        overlay = overlay.opts(legend_position='top')

        # グラフ共通のオプションを設定する
        overlay = HoloviewsBaseCommand.set_common_opts(overlay)

        # グラフをプロットする
        return self.make_plot(overlay)

class CsvToRepetitivieWaveCommand(HoloviewsBaseCommand):
    """
    反復波形図を出力する
    """
    def plot(self, args, column_names:list, matrix_dict:dict):
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

        # 初期表示時
        if x_axis_column is None and y_axis_column is None: 
            raise Exception(ErrMsg['1'])

        # 必須項目チェック
        if x_axis_column is None or y_axis_column is None or statics is None:
            return 

        # dfの作成
        df = pd.DataFrame(matrix_dict)

        # cleansing
        cleansing_df = self.doCleansing(df)

        keys = df.columns
        values = cleansing_df.columns
        dictionary = dict(zip(keys, values))

        # cleansing column_names (remove unvaild char like %)
        x_axis_column  = dictionary[x_axis_column]
        y_axis_column  = dictionary[y_axis_column]
        data_column = [dictionary[d] for d in data_column if d in dictionary.keys()]

        df = cleansing_df

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
                s = None
                for x in xs_event:
                    s = Span(location= x, dimension='height', line_color='black', line_dash='dashed', line_width=3, line_alpha=0.3)
                if s is not None:
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

        return gridplot(plots, ncols=1, sizing_mode='stretch_width', toolbar_location="right") 
    
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
        from bokeh.models.callbacks import CustomJS

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

    # TODO: この関数の処理内容が不明
    def doCleansing(self, df):
        i = df.values.tolist()
        i.insert(0,list(df.columns))
        result = None
        result <<= nm.mfldname(i=i, q=True).writelist(header=True)
        result = result.run()

        name = result.pop(0)
        result_df = pd.DataFrame(result,columns=name)

        return result_df

class CsvToTimeCompressionCommand(HoloviewsBaseCommand):
    """
    時間圧縮図を出力する
    """
    def plot(self, args, column_names:list, matrix_dict:dict):

        # 軸の設定
        x_axis         = args.get('x_axis')
        x_axis_column  = x_axis[0]['column']
        x_axis_label   = x_axis[0]['label']

        y_axis         = args.get('y_axis')
        y_axis_column  = y_axis[0]['column']
        y_axis_label   = y_axis[0]['label']

        # 初期表示時
        if x_axis_column is None and y_axis_column is None: 
            raise Exception(ErrMsg['1'])

        # データ系列の設定
        data     = args.get('data')   if args.get('data') is not None else []

        # グラフ表示要素の設定
        division        = args.get('division')
        statics         = args.get('statics')
        display_pattern = args.get('display_pattern')

        # df
        df = pd.DataFrame(matrix_dict, columns=column_names)
        
        # cleansing
        cleansing_df = self.doCleansing(df)

        keys = df.columns
        values = cleansing_df.columns
        dictionary = dict(zip(keys, values))

        # cleansing column_names (remove unvaild char like %)
        x_axis_column  = dictionary[x_axis_column]
        y_axis_column  = dictionary[y_axis_column]
        data = [dictionary[d] for d in data if d in dictionary.keys()]

        df = cleansing_df

        df[y_axis_column] = df[y_axis_column].astype(float)
        df[x_axis_column] = df[x_axis_column].astype(float)

        # title
        data_title = " ".join(data) if len(data) != 0 else "データ系列の指定なし"
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
            title = "{}:{}  期間:{} ~ {}  期間の分割数:{}".format(data_title, g, source[g]["x_range"][0], source[g]["x_range"][1], division)
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
                plot.line(source[g][result_column], source[g][statics], legend_label=statics, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2)
                if display_pattern == "hatch" and index + 1 < len(staticsArray):
                        x = source[g][result_column]
                        y1 = source[g][staticsArray[index]]
                        y2 = source[g][staticsArray[index + 1]]
                        plot.varea(x=x, y1=y1, y2=y2, fill_color='#cccccc', alpha=0.5)  

            plot.legend.location = "top_left"
            plot.legend.click_policy = "mute"
            plots.append(plot)

        return gridplot(plots, ncols=1, sizing_mode='stretch_width', toolbar_location="right") 

    def get_colors(self, size):
        i = 0
        colors = []
        for d in itertools.cycle(palette):
            if i >= size:
                break
            colors.append(d)
            i = i + 1

        return colors

    # TODO: この関数の処理内容が不明
    def doCleansing(self, df):
        i = df.values.tolist()
        i.insert(0,list(df.columns))
        result = None
        result <<= nm.mfldname(i=i, q=True).writelist(header=True)
        result = result.run()

        name = result.pop(0)
        result_df = pd.DataFrame(result,columns=name)

        return result_df

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
