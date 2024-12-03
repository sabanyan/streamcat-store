from setuptools import setup

setup(
    name='streamcat.store',
    packages=['streamcat.store'],
    version='3.3.1',
    description='Data Store of many type',
    url='https://www.kskp.io',
    install_requires=[
        # NOTE: macOS環境にpsycopg2のインストールを試みると、clangが "ld: library not found for -lssl"の
        # エラーメッセージを出力してインストールできない、代わりにpsycopg2-binaryをインストールする
        # NOTE: psycopg2-binaryはARM64環境に対応していない
        # 'psycopg2-binary',
        'psycopg2==2.9.6',
        'SQLAlchemy==2.0.13',
        'APScheduler==3.10.1',
        'jsonschema==4.17.3',
        # FastAPIへの移行により送出されるようになった例外(Can't pickle local object)を
        # 回避するためにmultiprocessを使用する
        'multiprocess==0.70.17',
        # 'alembic',
        'cryptography==40.0.2',
        'python-magic==0.4.27',
        'chardet==5.1.0',
        # 'awscli',
        # 'cx_Oracle',
        'numpy==1.24.3',
        'scipy==1.10.1',
        'pandas==2.0.1',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'matplotlib==3.7.1',
        'bokeh',
        'holoviews==1.16.0',
        'param==1.13.0'
    ],
)
