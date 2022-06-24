from setuptools import setup

setup(
    name='streamcat.store',
    packages=['streamcat.store'],
    version='3.1',
    description='Data Store of many type',
    url='https://www.kskp.io',
    install_requires=[
        # macOS環境にインストールすると、clangが "ld: library not found for -lssl"のエラーメッセージを出力して
        # インストールできない、そのためpsycopg2の代わりにpsycopg2-binaryをインストールする
        # 'psycopg2',
        'psycopg2-binary',
        'SQLAlchemy<1.5.0',
        'APScheduler',
        'jsonschema',
        # 'alembic',
        'cryptography',
        'python-magic',
        'chardet',
        'apache-beam',
        # 'awscli',
        # 'cx_Oracle',
        'numpy',
        'scipy',
        'pandas',
        'sklearn',
        # matplotlibとbokehはholoviewsが使用する
        'matplotlib',
        'bokeh',
        'holoviews',
        'param'
    ],
)
