# coding: utf8
from setuptools import setup, find_packages
from getsub.__version__ import __version__

setup(
    author="gyh1621",
    author_email="guoyh01@gmail.com",
    description="download subtitles easily",
    license="MIT",
    name='getsub',
    version=__version__,
    packages=find_packages(),
    install_requires=[    # 依赖列表
        'requests>=2.0',
        'bs4>=0.0.1',
        'guessit==3.0.3',
        'rarfile>=3.0',
        'backports.shutil-get-terminal-size>=1.0'
    ],
    entry_points={
        'console_scripts': [
            'getsub = getsub.main: main'
        ]
    },
    zip_safe=False,
    long_description=__doc__
)
