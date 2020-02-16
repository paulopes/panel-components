# -*- coding: utf-8 -*-

import os
import json

from .component import Component
from .tags import div, script


def vue_app(*children, template="", data={}, **attributes):

    # Vue.js app
    app_tag = div(auto_id=True)

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
        auto_id=True,
    )

    # Vue.js script
    app_tag.append_body_script(**{
        app_tag.id: '''
var app = new Vue({
  el: "#''' + app_tag.id + '''",
  template: "#''' + template_tag.id + '''",
  data: function() {
    return ''' + json.dumps(data) + '''
  }
});'''})

    # Vue.js library
    app_tag.asset_folders(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    )
    app_tag.append_body_js(vue="vue/vue.min.js")
    return Component(app_tag, template_tag)
