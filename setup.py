from setuptools import setup

setup(
    name='streamcat.store',
    packages=[
        'streamcat.core',
        'streamcat.depo',
        'streamcat.store'
    ],
    version='3.5',
    description='Data Store of many type',
    url='https://www.kskp.io',
    install_requires=[
        # NOTE: macOS環境にpsycopg2のインストールを試みると、clangが "ld: library not found for -lssl"の
        # エラーメッセージを出力してインストールできない、代わりにpsycopg2-binaryをインストールする
        # NOTE: psycopg2-binaryはARM64環境に対応していない
        # 'psycopg2-binary',
        'psycopg2==2.9.10',
        'SQLAlchemy==2.0.43',
        'APScheduler==3.11.0',
        'jsonschema==4.25.1',
        # FastAPIへの移行により送出されるようになった例外(Can't pickle local object)を
        # 回避するためにmultiprocessを使用する
        'multiprocess==0.70.18',
        # 'alembic',
        'cryptography==45.0.7',
        'python-magic==0.4.27',
        'chardet==5.2.0',
        # 'awscli',
        # 'cx_Oracle',
        'numpy==2.3.3',
        'scipy==1.16.2',
        'pandas==2.3.2',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'holoviews==1.21.0',
        'matplotlib==3.10.6',
        'bokeh==3.8.0',
        'param==2.2.1',
        'panel==1.8.0',
        # MYSOLを依存ライブラリに追加
        # 'mysol @ git+https://<TOKEN>@github.com/sabanyan/mysol.git@develop',
    ],
)
