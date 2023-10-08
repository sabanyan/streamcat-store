from setuptools import setup

setup(
    name='streamcat.store',
    packages=['streamcat.store'],
    version='3.3.3',
    description='Data Store of many type',
    url='https://www.kskp.io',
    install_requires=[
        # NOTE: macOS環境にpsycopg2のインストールを試みると、clangが "ld: library not found for -lssl"の
        # エラーメッセージを出力してインストールできない、代わりにpsycopg2-binaryをインストールする
        # NOTE: psycopg2-binaryはARM64環境に対応していない
        # 'psycopg2-binary',
        'psycopg2==2.9.7',
        'SQLAlchemy==2.0.21',
        'APScheduler==3.10.4',
        'jsonschema==4.19.1',
        # 'alembic',
        'cryptography==41.0.4',
        'python-magic==0.4.27',
        'chardet==5.2.0',
        # 'awscli',
        # 'cx_Oracle',
        'numpy==1.26.0',
        'scipy==1.11.3',
        'pandas==2.1.1',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'matplotlib==3.8.0',
        'bokeh==3.2.2',
        'holoviews==1.17.1',
        'param==1.13.0'
    ],
)
