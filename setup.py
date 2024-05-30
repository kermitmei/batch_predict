#!/usr/bin/env python

"""The setup script."""
import re

from setuptools import setup, find_packages

# 安装时依赖包
with open('llmbase/requirements.txt') as f:
    requirements = f.read().splitlines()
    # 过滤本地包和空行
    requirements = list(filter(lambda x: x and re.search(r'local', x) is None and not x.startswith('#'), requirements))
    # print(requirements)

setup(
    name='llmbase',
    version='1.0.0',
    packages=find_packages(),
    author="GuoXin",
    author_email='kermit.mei@gmail.com',
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.10'
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    install_requires=requirements,
    extras_require={},
    long_description='',
    include_package_data=True,
    keywords='llmbase',
    test_suite='tests',
    tests_require=[],
    url='https://www.chndata.com',
    zip_safe=False
)
