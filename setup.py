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
        'psycopg2',
        'SQLAlchemy<2.1.0',
        'APScheduler',
        'jsonschema',
        # 'alembic',
        'cryptography',
        'python-magic',
        'chardet',
        # 'awscli',
        # 'cx_Oracle',
        'numpy',
        'scipy',
        'pandas',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'matplotlib',
        'bokeh',
        'holoviews',
        'param'
    ],
)
