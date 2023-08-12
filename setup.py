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
        'psycopg2==2.9.7',
        'SQLAlchemy==2.0.19',
        'APScheduler==3.10.1',
        'jsonschema==4.19.0',
        # 'alembic',
        'cryptography==41.0.3',
        'python-magic==0.4.27',
        'chardet==5.2.0',
        # 'awscli',
        # 'cx_Oracle',
        'numpy==1.25.2',
        'scipy==1.11.1',
        'pandas==2.0.3',
        # K-Commandでのみ使用する
        'scikit-learn',
        # matplotlibとbokehはholoviewsが使用する
        'matplotlib==3.7.2',
        'bokeh==3.2.1',
        'holoviews==1.17.0',
        'param==1.13.0'
    ],
)
