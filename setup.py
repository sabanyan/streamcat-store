from setuptools import setup

setup(
    name='kskp.store',
    packages=['kskp.store'],
    description='Data Store of many type',
    url='https://www.ksk-anl.com/products/kskp',
    version_config={
        "version_format": '{tag}',
        "starting_version": '2.0.0'
    },
    setup_requires=['better-setuptools-git-version'],
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
