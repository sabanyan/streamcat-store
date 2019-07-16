#!usr/bin/bash -eu
#UTF-8, LF
#2019.02.04 Ryo Taniguchi
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.5"

# 
# オムロン結果データ集約用コマンド

# 機能
# 文字改行コード変更  UTF-8,LFへ
# 行方向結合    対象のファイルを行方向に結合する。
# ファイル名追加    行末に元ファイル名を新しい列(列名Filename)として追加する。
# 
# 入力　対象ファイルの指定
# テキストファイルでリストを与える。
# 
# 処理
# 1, 1ファイル目を読み込む
# 　  1行目を読んで、Filename列を行末に追加
# 　  2行目以降　元ファイル名を行末に追加して出力
# 　 
# 2、2ファイル目以降
# 　  1行目は読み飛ばす
# 　  2行目以降　元ファイル名を行末に追加し出力



function usage()
{
    echo " ${PROGNAME} : CSVファイルの集約 "
    echo "========================="
    echo "リストとして与えられたCSVファイル中のレコードの行末に元ファイル名を追加し、1つのファイルに集約して出力する。"
    echo "オプション指定"
    echo "f= 対象となるファイルのパスが、改行区切りで書かれたテキストファイル"
    echo "o= レコードを集約したファイル名。省略された場合は標準出力する。"
    echo "p= 作業ファイル格納パス名"
    echo "i= ダミーオプション。内部処理では使用しない。"
    echo "書式"
    echo "----"
    echo " ${PROGNAME} f= [o=] p= [i=] [--help] [--version]"

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

path_list="" # 対象ファイルのパスが書かれたテキストファイル名
result=""  # 適正レコード出力ファイル名
Tmp_path="" # 作業ファイル格納パス名

# 実装時テストデータ
# 1.ロジック確認
# path_list="/Users/taniguchiryo/Documents/集約テスト/Ibutsu_sample/ls_Ibutsu_test_0001.txt"
# result="/Users/taniguchiryo/Documents/集約テスト/Ibutsu_sample/v1_0001.csv"

param=""
for OPT in "$@"
do
    # echo $OPT
    case "${OPT}" in
        '-h' | '--help' )
            usage
            exit 1
            ;;
        '--version' )
            echo "${VERSION}"
            exit 1
            ;;
        'f='* )
            p_value=${1#*'='}   # =より前の文字を削除
            if [[ -z "${p=value}" ]] ; then
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            path_list=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        'o='* )
            p_value=${1#*'='}   # =より前の文字を削除
            if [[ -z "${p=value}" ]] ; then
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            result=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        'p='* )
            p_value=${1#*'='}   # =より前の文字を削除
            if [[ -z "${p=value}" ]] ; then
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            Tmp_path=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        'i='* )
            shift 1
            ;;
    esac
done

# 必須パラメータ指定なし fオプション
if [[ -z ${path_list} ]]; then
    echo "$PROGNAME: specify f= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi

# 必須パラメータ指定なし pオプション
if [[ -z ${Tmp_path} ]]; then
    echo "$PROGNAME: specify p= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi




# =o オプション指定無い場合、標準出力をセットする
if [[ -z ${result} ]]; then
    result='/dev/stdout'
fi

i=0 #処理ファイル数カウント
nkf -w -Lu -x  "${path_list}" | \
    while read file;
    do
        i=$(($i + 1))
        if [ $i = 1 ];
        then
            nkf -w -Lu -x "${Tmp_path}${file}" | \
            awk -v fn="${file}" -v result="${result}" \
                'BEGIN{FS=",";OFS=","}
                    {
                    if (NR==1)
                        {
                        print $0,"filename" >> result
                        }
                    else
                        {
                        print $0,fn >> result
                        }
                    }
                '
        #             #1行を読み込み、末尾にファイル名列を追加
        #             #2行目以降は行末にファイル名を追加する
        else
            nkf -w -Lu -x "${Tmp_path}${file}" | \
            awk -v fn="${file}" -v result="${result}" \
                'BEGIN{FS=",";OFS=","}
                    {
                    if (NR!=1)
                        {
                        print $0,fn >> result
                        }
                    }
                '
        #2ファイル目以降
        #             #1行以外を読み込み、行末にファイル名を追加して出力する
        fi    
    done
