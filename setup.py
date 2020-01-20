from setuptools import setup

setup(
    name='kskp.store',
    packages=['kskp.store'],
    install_requires=[
        'ordered_set',
        'psycopg2',
        'sqlalchemy',
        'alembic',
        'awscli',
        'cx_Oracle',
    ],
)
