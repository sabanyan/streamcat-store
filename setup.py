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
    ],
)
