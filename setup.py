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
        'psycopg2==2.9.10',
        'SQLAlchemy==2.0.27',
        'APScheduler==3.11.0',
        'jsonschema==4.23.0',
        # 'alembic',
        'cryptography==44.0.0',
        'python-magic==0.4.27',
        'chardet==5.2.0',
        # 'awscli',
        # 'cx_Oracle',
        'numpy==2.0.2',
        'scipy==1.13.1',
        'pandas==2.2.3',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'holoviews==1.20.0',
        'matplotlib==3.9.3',
        'bokeh==3.4.3',
        'param==2.1.1',
        'panel==1.4.5'
    ],
)
