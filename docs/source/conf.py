# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.
import sys

sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'S5')))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'S5'
copyright = '2024, Owen Foo'
author = 'Owen Foo'
from importlib.metadata import version as package_version

release = package_version("S5")

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

autosummary_generate = True
templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
# html_static_path = ['_static']


# useful article to generate class methods
# https://stackoverflow.com/questions/2701998/automatically-document-all-modules-recursively-with-sphinx-autodoc/62613202#62613202
