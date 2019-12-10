#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.1"

# 履歴
# 2019.02.19  修正 空白列1つのみのケース対応漏れを修正

#注意

#外部モジュール参照
# awk
#--------------------------------------------------------------
# column_blank_name
#--------------------------------------------------------------
function usage() {
    echo "${PROGNAME} ： 項目名ブランクの変更"
    echo "==========="
    echo " 空白の項目名に対して、指定した文字と重複時の識別子で"
    echo " 生成した項目名に変更し、全ての項目を出力する。"
    echo " 空白の項目名だけを対象とし、空白以外の項目名はそのまま出力する"
    echo
    echo " 空白の項目名が複数ある場合のデフォルトの項目名の変更"
    echo "   入力項目名： A,   ,B,   ,C"
    echo "   出力項目名： A,^^1,B,^^2,C"
    echo
    echo " b= 空白の列名であったことを意味する文字列を指定する"
    echo "    デフォルトは、ブランク"
    echo " d= 修辞句と元の項目名との区切り文字を指定する"
    echo "    デフォルトは ^^ 区切り"
    echo " -r 重複の識別子を、設備語でなく、接頭語として与える"
    echo " -n 重複の識別子を、重複した項目名別の連番でなく、項目名の先頭1始まりの順番とする"
    echo " i= 入力ファイル名を指定する。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} [b=] [d=] [-r] [-n] [i=] [o=] [--help] [--version]"
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
#   awk への -v 引数渡し の記述簡略化 のため
#   デフォルトが null or 0 となるようにする

blank=""        # b=
delimiter="^^"  # d=
sufix_off=0     # -r
dup_no_off=0    # -n
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
        'b='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            # 修辞句 ブランク も認める
            blank=${p_value}
            shift 1
            ;;
        'd='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            # 修辞句 ブランク も認める
            delimiter=${p_value}
            shift 1
            ;;
        '-r' )
            sufix_off=1
            shift 1
            ;;
        '-n' )
            dup_no_off=1
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
            echo "$PROGNAME: illegal option -- '$(echo $1 | sed 's/^-*//')'" 1>&2
            exit 1
            ;;
    esac
done

# 必須パラメータの指定無しのチェック
# if [[ -z ${} ]]; then
#     echo "$PROGNAME: specify f= argument" 1>&2
#     echo "Try '$PROGNAME --help' for more information." 1>&2
#     exit 1
# fi


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
awk -v b="${blank}" \
    -v d="${delimiter}" \
    -v r="${sufix_off}" \
    -v n="${dup_no_off}" \
'BEGIN{
  FS=","; OFS=",";
} # end of BEGIN
{
  if (NR==1) {
    # ヘッダーの解析
    #          1..NF   出現順番
    #   $i     1..NF   項目名
    #   fname [<名前>]  項目名をキーにしたし出現順番
    #   dup   [1..NF]  重複フラグ格納
    #   dup_no[1..NF]  重複項目別の連番
    #   last_i         最後の重複あった列の番号
    for (i=1; i<=NF; i++) {
      # 空白項目名だけ対象とする
      if ($i == "") {
        tmp[$i] += 1;
        last_i = i;
      }
      if (tmp[$i] == 2) {
        dup[ fname[$i] ] = 1;
        dup_no[ fname[$i] ] += 1;
      }
      if (tmp[$i] >= 2) {
        dup[i] = 1;
        dup_no[i] = tmp[$i];
      }
      fname[$i] = i;  # 同一項目名の前回の出現順番の記憶
    } # end of for i

    # 修正 空白列 1つのみのケース対応
    if (tmp[""] == 1) {
      dup[last_i] = 1;
      dup_no[last_i] = 1;
    }

    # デバッグ用 解析結果確認
    # for (i=1; i<=NF; i++) {
    #   print i, $i, dup[i], dup_no[i];
    # }

    # 変更名の生成
    for (i in dup) {
      str = ""
      # -n対応
      if (n == 0) { # 重複識別子 出現の連番
          str = dup_no[i];
        } else { # 重複識別子 列番号
          str = i;
        }
      # b= 対応
      if ( b != "" && $i == "" ) {
        $i = b;
      }
      # -r d= 対応
      if ( r == 0 ) { # 接尾語として付加
          $i = $i d str;
        } else {
          $i = str d $i;
        }
    } # end of for i

  } # end of if NR==1
  print $0;
}
' ${input_file} > "${output_file}"

exit 0
