from setuptools import setup

setup(
    name='kskp.store',
    packages=['kskp.store'],
    version='3.0',
    description='Data Store of many type',
    url='https://www.kskp.io',
    install_requires=[
        'psycopg2',
        'sqlalchemy',
        'alembic',
        'cryptography',
        'chardet',
        'awscli',
        'cx_Oracle',
        'numpy',
        'scipy',
        'pandas==0.24.2',
        'sklearn',
        # matplotlibはholoviewsが使用する
        'matplotlib',
        'holoviews==1.12.7',
        # param 1.10.0では以下のWarningが多量に表示される、bokehが参照している?
        # "WARNING:param.Dimension: Use method 'get_param_values' via param namespace"
        'param<=1.9.3',
        'bokeh==1.4.0',
    ],
)
