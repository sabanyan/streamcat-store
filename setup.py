from setuptools import setup

setup(
    name='kskp.store',
    packages=['kskp.store'],
    description='Data Store of many type',
    url='https://www.ksk-anl.com/products/kskp',
    install_requires=[
        'ordered_set',
        'chardet',
        'cryptography',
        'psycopg2',
        'sqlalchemy',
        'alembic',
        'awscli',
        'cx_Oracle',
    ],
)
