# -*- coding: utf-8 -*-
from __future__ import print_function, division

import sys
from .component import Component


def file_include(filename, *children, **attributes):
    component = Component(*children, **attributes)
    with open(filename) as f:
        file_contents = f.read()
    component.append_html(file_contents)
    return component
