from setuptools import find_packages, setup
from diffs import __version__

setup(
    name='django-diffs',
    version=__version__,
    url='https://github.com/linuxlewis/django-diffs',
    author='Sam Bolgert',
    author_email='sbolgert@gmail.com',
    description="Keep a record of diffs made to a Django model or collection of models",
    long_description=open('README.rst').read(),
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=1.8',
        'django-dirtyfields>=1.2',
        'six>=1.10.0',
        'redis>=2.10.5',
        'redisco==0.2.9'
    ],
    dependency_links=[
        'git://github.com/kiddouk/redisco.git@9a3e5102f2bc6449a2e7f2aa8eb7ec1b58453bd2#egg=redisco-0.2.9'
    ],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9'
    ]
)