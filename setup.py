from setuptools import setup
from pathlib import Path
from taskmn import __version__, __app_name__

directory = Path(__file__).parent
long_desc = (directory / "README.md").read_text(encoding="UTF-8")
setup(
    name=__app_name__,
    version=__version__,
    packages=['taskmn'],
    url='https://github.com/Drag-3/listmanager',
    license='',
    author='Drag',
    author_email='',
    description='Simple Cli Todo Manager w/ Typer',
    long_description=long_desc,
    install_requires=[
        "typer[all]~=0.7.0",
        "colorama",
        # "shellingham",
        # "rich~=13.3.1",
        "click~=8.1.3"
    ],
    entry_points={
        'console_scripts': ['taskmn = taskmn.__main__:main']
    }
)
