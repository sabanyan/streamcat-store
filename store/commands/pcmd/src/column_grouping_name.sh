#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.0"

#注意
# 列番号指定は、未対応
# オプション指定の整合性チェックは、未対応

#外部モジュール参照
# awk
#--------------------------------------------------------------
# column_grouping_name
#--------------------------------------------------------------
function usage() {
    echo "${PROGNAME} ： グループ化列名"
    echo "==========="
    echo " 項目群に対して、グループに属する項目名に接頭語を付与する。"
    echo "    例 f=A:G1,A:G2"
    echo "    最初の項目Aの次の項目から、2番目の項目Aの前までの項目に、G1 を付加し、"
    echo "    2番目の項目Aの次から最後の項目に、G2 を付加する"
    echo
    echo " f= 項目グループの開始項目名：列グループ名 のリストを、カンマ区切りで指定する"
    echo " O= 項目グループの終了項目名リストを、カンマ区切りで指定する"
    echo "    省略時は、次の項目グループの開始項目の前項目を終わりとする"
    echo " d= 修辞句と元の項目名との区切り文字を指定する"
    echo "    デフォルトは _ 区切り"
    echo " -r 項目グループ名を、接頭語でなく、接尾語として与える"
    echo " -R 項目グループの開始項目へも 修辞句 を付与する"
    echo " i= 入力ファイル名を指定する。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} f= [O=] [d=] [-r] [-R] [i=] [o=] [--help] [--version]"
    echo

    exit 1
}

# エラー処理
set -e -u -o pipefail   # パイプ処理中にエラー発生で処理を終了する設定
error(){
  echo "#ERROR# Stoped ${PROGNAME}"
  echo "[ ${BASH_SOURCE} : ${LINENO} ] returns not zero status"
  exit 1
}
trap error ERR

# 引数格納用変数
colum_group_list=""
colum_group_end_list=""
delimiter="_"
prefix_on=1
group_start_on=0
input_file=""
output_file=""

# 参考 引数処理： https://qiita.com/b4b4r07/items/dcd6be0bb9c9185475bb
for OPT in "$@"
do
#  echo $OPT
    case "$OPT" in
        '-h'|'--help' )
            usage
            exit 1
            ;;
        '--version' )
            echo ${VERSION}
            exit 1
            ;;
        'i='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            input_file=${p_value}
            shift 1
            ;;
        'o='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            output_file=${p_value}
            shift 1
            ;;
        'f='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            colum_group_list=${p_value}
            shift 1
            ;;
        'O='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            colum_group_end_list=${p_value}
            shift 1
            ;;
        'd='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            # 修辞句 ブランク も認める
            delimiter=${p_value}
            shift 1
            ;;
        '-r' )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            prefix_on=0
            shift 1
            ;;
        '-R' )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            group_start_on=1
            shift 1
            ;;
        '--'|'-' )
            shift 1
            break
            ;;
        -*)
            echo "$PROGNAME: illegal option -- '$(echo $1 | sed 's/^-*//')'" 1>&2
            exit 1
            ;;
        *)
            if [[ ! -z "$1" ]] && [[ ! "$1" =~ ^-+ ]]; then
               shift 1
            fi
            ;;
    esac
done

# 必須パラメータ指定無し
if [[ -z ${colum_group_list} ]]; then
    echo "$PROGNAME: specify f= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi


# 準備処理
# i= 指定が無い場合、標準入力をセットする
if [[ -z ${input_file} ]]; then
  input_file='/dev/stdin'
fi

# o= 指定が無い場合、標準出力をセットする
if [[ -z ${output_file} ]]; then
  output_file='/dev/stdout'
fi

# データ処理
awk -v f="${colum_group_list}" \
    -v O="${colum_group_end_list}" \
    -v d="${delimiter}" \
    -v r="${prefix_on}" \
    -v R="${group_start_on}" \
'BEGIN{
  FS=","; OFS=",";
  g_num     = split(f, group, ",");     #格納 group[],    g_num
  g_end_num = split(O, group_end, ","); #格納 group_end[],g_end_num

  # 引数の整合性チェック
  # << 未実装 >>
}
{
    if (NR==1) {
      # グループ列開始と明示的な終了列の判定
      search = 1;
      for (i=1;i<=g_num;i++) {
        g_i_num = split(group[i], g,":"); #格納 g[], g_i_num
        g_r[i]  = g[2];
        if (g_i_num != 2) { exit 1; }

          for (j=search; j<=NF; j++) {
            if ($j != "" && $j == g[1]) {
              g_col_s[i] = j;            #格納 g_col_s[]
              search = j+1;
              break;
            }
          } # end of for j FS
      } # end of for i group

      # 暗黙のグループ終了列の判定
      for (i=1;i<=g_num;i++) {
        if (g_col_e[i] == "" ) {
          if (i<g_num && g_col_s[i+1]!= "" ) {
            g_col_e[i] = g_col_s[i+1] - 1;
          } else {
            g_col_e[i] = NF;
          }
        }
      } # end of for i

      # 明示的なグループ終了列の判定
      for (i=1; i<=g_num; i++) {
        for (k=g_col_s[i]; k<=g_col_e[i]; k++) {
            if ($k != "" && $k == group_end[i]) { g_col_e[i] = k } #格納 g_col_e[]
        }
      }

      # 列名の変更
      for (i=1; i<=g_num; i++) {
        for (k=g_col_s[i]+1; k<=g_col_e[i]; k++) {
          if (r == 1) {
              $k = g_r[i] d $k;
          } else {
              $k = $k d g_r[i];
          }
        } # end of for k
        if (R == 1) {
          if (r == 1) {
              $g_col_s[i] = g_r[i] d $g_col_s[i];
          } else {
              $g_col_s[i] = $g_col_s[i] d g_r[i];
          }
        }
      } # end of for i group

      print $0;
    } # end of header
  else {
    print $0;
  }
}
' ${input_file} > "${output_file}"

exit 0
