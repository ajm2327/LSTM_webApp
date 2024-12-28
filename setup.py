from setuptools import setup, find_packages

setup(
    name="lstm_tool",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'apscheduler',
        'redis',
        'yfinance',
        'pandas',
        'numpy',
        'tensorflow',
        'scikit-learn'
    ]
)
