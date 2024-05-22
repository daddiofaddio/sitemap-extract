from setuptools import setup, find_packages

setup(
    name='sitemap_extract',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'cloudscraper==1.2.58',
        'argparse==1.4.0',
    ],
    entry_points={
        'console_scripts': [
            'sitemap_extract=sitemap_extract.sitemap_extract:main',
        ],
    },
)
