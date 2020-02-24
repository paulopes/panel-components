# -*- coding: utf-8 -*-

import os
import json

from .component import Component
from .tags import div, script


def vue(*children, template="", main=None, **attributes):

    # Vue.js app
    app_tag = div()

    # Vue.js template
    # We use an x-template script tag instead of a template tag because:
    # - The browser doesn't waste CPU cycles parsing its DOM unecessarily;
    # - We can use PascalCase and camelCase Vue components;
    # - We avoid search engine inclusion of template syntax;
    # - We don't conflict with Web Component libraries we may also be using;
    # - An x-template script tag works in IE11, in case we come across it.
    template_tag = script(
        div(*children, **attributes).prepend_html(template),
        type="text/x-template",
    )

    component = Component(app_tag, template_tag, main=main)

    component.data_prefix = '''
var app = new Vue({
  el: "#''' + app_tag.id + '''",
  template: "#''' + template_tag.id + '''",
  data: {
    '''
    component.data_postfix = '''
  }
});'''
    
    component.asset_folders(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    )
    component.append_body_js(vue="vue/vue.min.js")

    return component
