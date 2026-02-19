from setuptools import setup

setup(
    name='streamcat.store',
    packages=[
        'streamcat.core',
        'streamcat.depo',
        'streamcat.store'
    ],
    version='3.6',
    description='Data Store of many type',
    url='https://www.kskp.io',
    install_requires=[
        # NOTE: macOS環境にpsycopg2のインストールを試みると、clangが "ld: library not found for -lssl"の
        # エラーメッセージを出力してインストールできない、代わりにpsycopg2-binaryをインストールする
        # NOTE: psycopg2-binaryはARM64環境に対応していない
        # 'psycopg2-binary',
        'psycopg2==2.9.11',
        'SQLAlchemy==2.0.46',
        'APScheduler==3.11.2',
        'jsonschema==4.26.0',
        # FastAPIへの移行により送出されるようになった例外(Can't pickle local object)を
        # 回避するためにmultiprocessを使用する
        'multiprocess==0.70.19',
        # 'alembic',
        'cryptography==46.0.5',
        'python-magic==0.4.27',
        'chardet==5.2.0',
        # 'awscli',
        # 'cx_Oracle',
        'numpy==2.4.2',
        'scipy==1.17.0',
        'pandas==3.0.1',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'holoviews==1.22.1',
        'matplotlib==3.10.8',
        'bokeh==3.8.2',
        'param==2.3.2',
        'panel==1.8.7'
    ],
)
