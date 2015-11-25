#!/usr/bin/env python

from setuptools import setup

# To build:
# python setup.py sdist
# python setup.py bdist_wheel
#
# To install:
# python setup.py install
#
# To register (only needed once):
# python setup.py register
#
# To upload:
# python setup.py sdist upload
# python setup.py bdist_wheel upload

setup(
    name='cortanaanalytics',
    version='0.0.2',
    description='Wrappers of Cortana Analytics services',
    license='Apache License 2.0',
    author='Microsoft Corporation',
    author_email='ptvshelp@microsoft.com',
    url='https://github.com/crwilcox/cortanaanalytics',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: Apache Software License',
    ],
    packages=['cortanaanalytics'],
    install_requires=[
        'requests',
    ],
    zip_safe = False,
)
