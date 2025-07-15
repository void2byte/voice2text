#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Установочный скрипт для проекта голосового ввода.
"""

from setuptools import setup, find_packages
import os

# Читаем README файл
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Читаем requirements.txt
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='voice2text',
    version='1.0.0',
    description='Система голосового ввода с поддержкой множественных API распознавания речи',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Voice2Text Team',
    author_email='support@voice2text.com',
    url='https://github.com/voice2text/voice2text',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='speech recognition voice input yandex vosk google cloud',
    entry_points={
        'console_scripts': [
            'voice2text=main:main',
            'voice2text-gui=run_speech_recognition:main',
        ],
    },
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'google': [
            'google-cloud-speech>=2.0.0',
            'google-auth>=2.0.0',
        ],
        'vosk': [
            'vosk>=0.3.45',
        ],
        'all': [
            'google-cloud-speech>=2.0.0',
            'google-auth>=2.0.0',
            'vosk>=0.3.45',
        ],
    },
)