from setuptools import setup

setup(
    name="pydiceparse",
    version="0.1",
    author="Alex Walters",
    author_email="tritium@sdamon.com",
    description=("Dice syntax parser and roller"),
    license="BSD",
    py_modules=["diceparse"],
    install_requires=[
        'pyparsing',
    ],
    entry_points={
        'console_scripts': {
            'pydice = diceparse:main'
        }
    }
)
