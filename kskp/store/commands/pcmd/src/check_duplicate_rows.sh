#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.2"

#外部モジュール参照
# MCMD使用

#未実装箇所
# 列名無しの列番号指定は、未対応

#--------------------------------------------------------------
# check_duplicate_rows
#--------------------------------------------------------------
# キー項目別の連番を振り、連番が0始まりで1以上のものを重複として、抽出する
#
# 補足
#   名前付きパイプを用いた ファイルを使用しないパイプ処理も試みたが
#   複数のプロセスを同期することができないため断念。
#
#   → 入力ファイルを、一時ファイルへコピーする方法で実装

function usage() {
    echo "${PROGNAME} ： 重複行の抽出"
    echo "==========="
    echo " NYSOL MCMDを用いてキー項目が重複する行を抽出する"
    echo
    echo " k= キー項目をカンマ区切りで与える"
    echo " i= 入力ファイル名を指定する。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo " tmpPath= 作業用のフォルダパス名を指定する。省略時は、カレントフォルダへ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} k=  [i=] [o=] [tmpPath=] [--help] [--version]"
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
key_colums=""
input_file=""
output_file=""
tmp_path=""

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
        'tmpPath='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            tmp_path=${p_value}
            shift 1
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
        'k='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            key_colums=${p_value}
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
if [[ -z ${key_colums} ]]; then
    echo "$PROGNAME: specify k= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi

# 定数
readonly COLUM_NAME_DUPLICATION='__dup_total__'   #重複数
readonly COLUM_NAME_ROW_NO='__RowNo_BeginWith1__'  #1始まりの行番号
readonly COLUM_NAME_DUPLICATION_NO='__dup_no__'   #重複の連番

readonly TMP_FILE_NAME="/home/kskp/kskp/data/tmp/tmp.csv"
readonly TMP_INPUT_NAME="/home/kskp/kskp/data/tmp/input.csv"


# -qオプションで、キー項目の %数字 列名を除去するための列名変更リストの生成
#   入力例： key_colums               key1,key2
#   出力例： key_colums_rename_list   key1:key1,key2:key2
key_colums_rename_list=''
top_flg=1
for i in ${key_colums//,/ }; do
  if [ ${top_flg} == 1 ]; then
    key_colums_rename_list="${i}"':'"${i}"
    top_flg=0
  else
    feature_list_1="${key_colums_rename_list}"','"${i}"':'"${i}"
  fi
done

# 準備処理
# i= 指定が無い場合、標準入力をセットする
if [[ -z ${input_file} ]]; then
  input_file='/dev/stdin'
fi

# o= 指定が無い場合、標準出力をセットする
if [[ -z ${output_file} ]]; then
  output_file='/dev/stdout'
fi

# 作業用ファイル名
tmp_file=""
if [[ -z ${tmp_path} ]]; then
  tmp_file="${TMP_FILE_NAME}"
else
  if [[ "${tmp_path: -1}" == '/' ]]; then  # 変数最後の1文字 -1の前に空白要に注意
    tmp_file="${tmp_path}${TMP_FILE_NAME}"
  else
    tmp_file="${tmp_path}/${TMP_FILE_NAME}"
  fi
fi

# データ処理
# isnull(${'"${COLUM_NAME_DUPLICATION}"'})
#
mcal      i="${input_file}" \
          c='line()+1' \
          a="${COLUM_NAME_ROW_NO}" \
          -assert_diffSize | \
mtee      o="${tmp_file}"  | \
mcut      f="${key_colums}" | \
mnumber   a="${COLUM_NAME_DUPLICATION}" \
          k="${key_colums}" \
          s="${key_colums}" \
          S=1 \
          -assert_diffSize \
          -assert_nullkey | \
msel      c='${'"${COLUM_NAME_DUPLICATION}"'}>=2' | \
mstats    k="${key_colums}" \
          f="${COLUM_NAME_DUPLICATION}" \
          c="max" | \
mnjoin    m="${tmp_file}" \
          k="${key_colums}" | \
mnumber   a="${COLUM_NAME_DUPLICATION_NO}" \
          k="${key_colums}" \
          s="${key_colums}" \
          S=1 \
          -assert_diffSize \
          -assert_nullkey | \
mfldname  f="${key_colums_rename_list}" \
          o="${output_file}" \
          -q \
          -assert_diffSize

# 後処理
rm "${tmp_file}"

exit 0
