from setuptools import setup

setup(
    name='streamcat.store',
    packages=['streamcat.store'],
    version='3.4',
    description='Data Store of many type',
    url='https://www.kskp.io',
    install_requires=[
        # NOTE: macOS環境にpsycopg2のインストールを試みると、clangが "ld: library not found for -lssl"の
        # エラーメッセージを出力してインストールできない、代わりにpsycopg2-binaryをインストールする
        # NOTE: psycopg2-binaryはARM64環境に対応していない
        # 'psycopg2-binary',
        'psycopg2==2.9.9',
        'SQLAlchemy==2.0.23',
        'APScheduler==3.10.4',
        'jsonschema==4.20.0',
        # 'alembic',
        'cryptography==41.0.5',
        'python-magic==0.4.27',
        'chardet==5.2.0',
        # 'awscli',
        # 'cx_Oracle',
        'numpy==1.26.2',
        'scipy==1.11.4',
        'pandas==2.1.3',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'matplotlib==3.8.2',
        'bokeh==3.3.0',
        'holoviews==1.18.1',
        'param==2.0.1'
    ],
)
