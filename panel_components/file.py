# -*- coding: utf-8 -*-
from __future__ import print_function, division

import sys
from .component import Component


def file(filename, *children, **attributes):
    component = Component(**attributes)
    with open(filename) as f:
        file_contents = f.read()
    component.append_children(children).append_html(file_contents)
    return component
