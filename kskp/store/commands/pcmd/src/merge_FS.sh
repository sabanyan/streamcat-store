#!/bin/bash -eu
#UTF-8, LF
#2019.02.04 Ryo Taniguchi
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.4"
# オムロンFSデータ集約用コマンド

# 機能
# 文字改行コード変更  UTF-8,LFへ
# 列数補完  不足している列名行を空欄で補完する。
# 行方向結合    対象のファイルを行方向に結合する。
# ファイル名追加    行末に元ファイル名を新しい列(列名Filename)として追加する。
# レコードの適/不適判断　不適切なレコードを列数をもとに判断して分けて出力する。
# 
# 入力　対象ファイルの指定
# テキストファイルでリストを与える。
# 
# 処理
# 1、適切な列数を決める。
#    最初のファイルを指定行数処理して、もっとも出現頻度が高い列数を適切な列数とする。
#     もっとも出現頻度が高い列数が複数ある場合は、もっとも大きい列数を適切な列数とする。
#     最初のファイルの行数が100件に満たない場合は、最終行までを処理する。
# 
# 2、列名行を修正し、出力する。
#    不足しているコンマと、Filename列を追加してファイルへ出力する。
# 　   列名は最初のファイルの先頭行から引用する。
# 3、レコードを処理する。
#     適正列数か否かを判断して、出力先を分ける。出力の末尾にはファイル名を追記する。


function usage()
{
    echo " ${PROGNAME} : 不整CSVファイルのクレンジングと集約 "
    echo "========================="
    echo "リストとして与えられたCSVファイル中のレコードの行末に元ファイル名を追加し、1つのファイルに集約して出力する。"
    echo "集約の過程で以下のデータクレンジング処理を行う"
    echo "1、Headerの列数とレコードの列数を比較し、Headerの列数が少ない場合に空白列名を追加する。"
    echo "2、不適正な列数のレコードを除く。不適正レコードは適正なレコードと分けて出力する。"
    echo "   適正なレコードは列数で判断し、対象ファイルリストの先頭から指定行数までの列数最頻値を適正レコードの列数とする。"
    echo "   複数の列数が最頻値となっている場合は、その中で最大の列数を適正値とする。"
    echo ""
    echo "オプション指定"
    echo "f= 対象となるファイルのパスが、改行区切りで書かれたテキストファイル。"
    echo "o= 列数が適正と判断されたレコードを集約したファイル名を指定する。省略時は標準出力する。"
    echo "e= 列数が不適正と判断されたレコードを集約したファイル名を指定する。"
    echo "s= 適正な列数を判断すために参照するレコード数"
    echo "p= 作業ファイル格納パス名"
    echo "i= ダミー。内部処理には使用しない"
    echo ""
    echo "書式"
    echo "----"
    echo " ${PROGNAME} f= [o=] e= s= p= [i=] [--help] [--version]"

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




# # 実装時の参照データ
# # 1.ロジック確認・検証
# target_file_list="/Users/taniguchiryo/Documents/testdata/Sjis_CRLF/list_file.txt" #対象ファイルのフルパスが書かれたテキスト
# result="/Users/taniguchiryo/Documents/testdata/Sjis_CRLF/res.csv" #出力先ファイル名
# target_file="/Users/taniguchiryo/Documents/testdata/testdata_err.csv"
# Seq_record="10" # 適正列数を決めるために参照するレコードの行数

# # 2.サンプルファイルの一部を使った検証


# # 3.サンプルファイル全てを対象とした検証　in CentOS サーバ
# abs_path="/home/kskp-trial/KSKP_trial"
# target_file_list="${abs_path}/20181129_omron_original_copy/データ/filelist_FS_組立#1.txt" #対象ファイルのフルパスが書かれたテキスト
# result_correct="${abs_path}/20181129_omron_original_copy/データ/2.FS/FS_組立#1.csv" #出力先ファイル名
# result_defect="${abs_path}/20181129_omron_original_copy/データ/2.FS/FS_組立#1_irreguler.csv"

# Seq_record="10000" # 適正列数を決めるために参照するレコードの行数

# エラー処理（未実装）

# 引数格納用変数、デフォルト設定
target_file_list="" # 対象ファイルのパスが書かれたテキストファイル名
result_correct=""  # 適正レコード出力ファイル名
result_defect="" # 不適正レコード出力ファイル名
Seq_record="" # 適正レコードの列数を決めるために参照するレコード数
Tmp_path="" # 作業ファイル格納パス

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
            target_file_list=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        'o='* )
            p_value=${1#*'='}   # =より前の文字を削除
            if [[ -z "${p=value}" ]] ; then
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            result_correct=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        'e='* )
            p_value=${1#*'='}   # =より前の文字を削除
            if [[ -z "${p=value}" ]] ; then
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            result_defect=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        "p="* )
            p_value=${1#*'='}   # =より前の文字を削除
            if [[ -z "${p=value}" ]] ; then
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            Tmp_path=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        's='* )
            p_value=${1#*'='}   # =より前の文字を削除
            if [[ -z "${p=value}" ]] ; then
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            Seq_record=${p_value}
            param+=( "$@" )
            shift 1
            ;;
        'i='* )
            shift 1
            ;;
    esac
done

# 必須パラメータ指定なし fオプション
if [[ -z ${target_file_list} ]]; then
    echo "$PROGNAME: specify f= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi

# 必須パラメータ指定なし eオプション
if [[ -z ${result_defect} ]]; then
    echo "$PROGNAME: specify e= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi

# 必須パラメータ指定なし　sオプション
if [[ -z ${Seq_record} ]]; then
    echo "$PROGNAME: specify s= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi

# 必須パラメータ指定なし　pオプション
if [[ -z ${Tmp_path} ]]; then
    echo "$PROGNAME: specify p= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi




# 準備処理
# o= 指定が無い場合、標準出力をセットする。
if [[ -z ${result_correct} ]]; then
    result_correct='/dev/stdout'
fi


# 参照行数
Seq_record=$(($Seq_record + 1)) # 参照行数に先頭行分を追加する。

# 1、適正な列数を決める
# 対象ファイルリストの1行目を読みこむ。
head -n 1 "${target_file_list}" | nkf -w -Lu -x | \
{ \
# 読み込んだファイルパスを変数にする。
read target_file;
    head -$Seq_record "${Tmp_path}${target_file}" | nkf -w -Lu -x | \

# # # awk内の処理　適正列数を決めるため、最頻値を求める。
# 
# 1、行番号をインデックス、列数を要素に持つ配列を作成する。
# 2、列数をインデックス、インデックスの列数の行数を要素に持つ配列をつくる。
# 3、インデックスの列数の行数の最頻値を求め、その列数を返す。
# 　 複数の列数が最頻値となった場合は、列数を比較し、大きいほうを適正な列数として出力する。

   awk -v Seq_record=$Seq_record \
    '
    BEGIN{FS=",";OFS=","} 
    {
    if(NR != 1 && NR <= Seq_record)
        {nf[NR]=NF}
    }
    END{itr=0;
        for(i in nf)
            {itr++;
            if(itr==1)
                {
                n_col[nf[i]]=1
                }
            else
                {
                if (n_col[nf[i]] == "")
                    {
                    n_col[nf[i]] = 1
                    }
                else
                    {
                    n_col[nf[i]]++
                    }
                }
            }
        col_fq_max=0;col_num_correct=0;
        for(j in n_col)
            {
            if(col_fq_max + 0 < n_col[j] + 0)
                {
                col_fq_max=n_col[j];
                col_num_correct=j;
                }
            else if(col_fq_max + 0 == n_col[j] + 0)
                {
                if(col_num_correct + 0 < j + 0)
                    {
                    col_num_correct=j
                    }
                }
            }
        print col_num_correct
        }
    ' | \
    {
    read col_num_correct; # 適正な列数を変数に入れる。
        head -1 "${Tmp_path}${target_file}" | nkf -w -Lu -x | \

    # # awk内の処理　適正行を出力
    # # 1列目の内容を取得し、改行コードを削除して変数へ代入
    # # 2列目NFと1列目NFの差の分 -1 個の"," を繰り返した変数xをつくる。
    # # 変数col(1行目の内容)、変数x(不足している",") 、filenameをファイルへ出力する。
    awk -v col_num_correct=$col_num_correct -v result_correct="${result_correct}" \
    '
    BEGIN{FS=",";OFS=","} 
    {
    if(NR==1)
        {
        col_name=$0
            {
            if(NF + 0 < col_num_correct + 0)
                {
                fs_add = col_num_correct - NF;
                for(i=1;i<fs_add;i++)x=x",";
                print col_name,x,"filename" >> result_correct
                }
            }
        }
    }
    ' 


    # レコードを読み込む
    nkf -w -Lu -x "${target_file_list}" | \
        while read file;
        do
            nkf -w -Lu -x "${Tmp_path}${file}" | \
            awk -v fn="${file}" -v col_num_correct=$col_num_correct \
                -v result_correct="${result_correct}" -v result_defect="${result_defect}" \
            '
            BEGIN{FS=",";OFS=","}
            {
            if(NR!=1)
                {
                if(NF + 0 == col_num_correct + 0)
                    {
                    print $0,fn >> result_correct
                    }
                else
                    {
                    print $0,fn >> result_defect
                    }
                }
            }
            '
            #1行以外を読み込み、行末にファイル名を追加して出力する。
        done
    # 適正レコードのみ出力(ver 0.0)
    # cat "${target_file_list}" | nkf -w -Lu -x | \
    #     while read file;
    #     do
    #         # 適正レコードのみ処理して出力
    #         nkf -w -Lu -x "${file}" | \
    #         awk -v fn="${file}" -v col_num_correct=$col_num_correct \
    #         '
    #         BEGIN{FS=",";OFS=","}
    #         {
    #         if(NR!=1 && NF + 0 == col_num_correct + 0)
    #             {
    #             print $0,fn >> 
    #             }
    #         }
    #         ' >> "${result_correct}"

    #         # # 不適正レコードのみ処理して出力
    #         # nkf -w -Lu -x "${file}" | \
    #         # awk -v fn="${file}" -v col_num_correct=$col_num_correct \
    #         # '
    #         # BEGIN{FS=",";OFS=","}
    #         # {
    #         # if(NR!=1 && NF + 0 != col_num_correct + 0)
    #         #     {
    #         #     print $0,fn
    #         #     }
    #         # }
    #         # ' >> "${result_defect}"
    #     done
    }
}
