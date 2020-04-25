from setuptools import setup


def read(fname):
    with open(fname, 'r') as f:
        return f.read()


setup(
    name="pydiceparse",
    version="0.4.2.2",
    author="Alex Walters",
    author_email="tritium@sdamon.com",
    description=("Dice syntax parser and roller"),
    long_description=read('README.rst'),
    url='https://github.com/tritium21/pydiceparse',
    license="BSD",
    py_modules=["diceparse"],
    install_required=[
        'lark-parser>=0.6.3'
    ],
    entry_points={
        'console_scripts': {
            'pydice = diceparse:main'
        }
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ]
)
