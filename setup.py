# setup.py
import subprocess
import sys
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        self.install_playwright()

    def install_playwright(self):
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])

class PostDevelopCommand(develop):
    def run(self):
        develop.run(self)
        self.install_playwright()

    def install_playwright(self):
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vitam-paper-prep',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A tool for processing academic paper references',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/VITAM_paper_prep',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'beautifulsoup4',
        'PyMuPDF',
        'playwright==1.36.0',
        'fake-useragent',
        'markdownify',
        'requests',
    ],
    extras_require={
        'dev': ['pytest', 'pytest-asyncio'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'process_references=paper_prepper.reference_processor:main',
        ],
    },
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)