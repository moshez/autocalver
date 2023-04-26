# Copyright (c) Shopkick
# See LICENSE for details.
import os
import sys

up = os.path.dirname(os.path.dirname(__file__))
sys.path.append(up)

import autocalver

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]
master_doc = 'index'
project = 'Autocalver'
copyright = 'Moshe Zadka'
author = 'Moshe Zadka'
version = release = str(autocalver.__version__)

exclude_patterns = [".ipynb_checkpoints/*"]
