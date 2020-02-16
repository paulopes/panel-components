# -*- coding: utf-8 -*-
from __future__ import print_function, division

try:
    from io import StringIO
except NameError:
    from StringIO import StringIO

import matplotlib.pyplot as plt

from .component import Component


def plt_snapshot(**attributes):
    component = Component(**attributes)
    f = StringIO()
    plt.savefig(f, format="svg")
    xml = f.getvalue()
    svg = xml[xml.index("<svg"):]
    component.append_html(svg)
    return component
