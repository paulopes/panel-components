# -*- coding: utf-8 -*-
from __future__ import print_function, division

import html
import uuid
import json
import itertools

import panel as pn

from .utils import (
    IS_A_JUPYTER_NOTEBOOK,
    is_a_number,
    template_escape,
    get_dir_name,
    get_inline_js,
    get_inline_css,
    make_available,
    can_make_inline_uri,
    make_inline_uri,
)

try:
    from urllib.parse import urlsplit
except:
    from urlparse import urlsplit


# Not relying on panel to include pyviz resources, except while running
# inside Jupyter, because sometimes when panel is serving multiple notebooks
# simultaneously panel will include in a notebook page resources that are
# only needed in pages of other notebooks.
PYVIZ_EXTENSIONS = {
    "bokeh": {
        "css": {
            "cdn": ["bokeh/panel.css",],  # Not on a CDN
            "local": ["bokeh/panel.css",],
        },
        "js": {
            "cdn": [
                "//cdnjs.cloudflare.com/ajax/libs/bokeh/1.4.0/bokeh.min.js",
                "//cdnjs.cloudflare.com/ajax/libs/bokeh/1.4.0/bokeh-widgets.min.js",
                "//cdnjs.cloudflare.com/ajax/libs/bokeh/1.4.0/bokeh-tables.min.js",
                "//cdnjs.cloudflare.com/ajax/libs/bokeh/1.4.0/bokeh-gl.js",
                "bokeh/panel.min.js",  # Not on a CDN
            ],
            "local": [
                "bokeh/bokeh.min.js",
                "bokeh/bokeh-widgets.min.js",
                "bokeh/bokeh-tables.min.js",
                "bokeh/bokeh-gl.min.js",
                "bokeh/panel.min.js",
            ],
        },
    },
    "katex": {
        "css": {
            "cdn": ["//cdnjs.cloudflare.com/ajax/libs/KaTeX/0.6.0/katex.min.css",],
            "local": ["katex/katex.css",],
        },
        "js": {
            "cdn": [
                "//cdnjs.cloudflare.com/ajax/libs/KaTeX/0.6.0/katex.min.js",
                "//cdn.jsdelivr.net/npm/katex@0.10.1/dist/contrib/auto-render.min.js",
            ],
            "local": ["katex/katex.min.js", "katex/auto-render.min.js",],
        },
    },
    "mathjax": {
        "js": {
            "cdn": [
                "//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-MML-AM_CHTML",
            ],
            "local": ["mathjax/mathjax_tex-mml-am_chtml.js",],
        },
    },
    "plotly": {
        "js": {
            "cdn": [
                "//cdn.plot.ly/plotly-latest.min.js",
                "//cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.15/lodash.min.js",
            ],
            "local": ["plotly/plotly.min.js", "plotly/lodash.min.js",],
        },
    },
    "vega": {
        "js": {
            "cdn": [
                "//cdn.jsdelivr.net/npm/vega@5",
                "//cdn.jsdelivr.net/npm/vega-lite@3",
                "//cdn.jsdelivr.net/npm/vega-embed@6",
            ],
            "local": ["vega/vega.js", "vega/vega-lite.js", "vega/vega-embed.js",],
        },
    },
    "vtk": {"js": {"cdn": ["//unpkg.com/vtk.js",], "local": ["vtk/vtk.js",],},},
    "ace": {
        "js": {
            "cdn": [
                "//cdnjs.cloudflare.com/ajax/libs/ace/1.4.3/ace.js",
                "//cdnjs.cloudflare.com/ajax/libs/ace/1.4.3/ext-language_tools.js",
            ],
            "local": ["vtk/vtk.js",],
        },
    },
}


def make_tag_function(tag, xml_closing_style=False):
    """Generate a function that returns a component for an html tag."""

    def tag_function(*children, **attributes):
        if xml_closing_style and not children:
            component = Component(opening="<" + tag + "/>", **attributes)
        else:
            component = Component(
                *children,
                opening="<" + tag + ">",
                closing="</" + tag + ">",
                **attributes
            )
        return component

    return tag_function


class Component:
    """Encapsulates all the html content, css and js requirements, as well as
    methods that assist in creating and generating a template (or html partial)
    for a component of a page that will served by a Panel server."""

    def __init__(
        self,
        *children,
        tag_name=None,
        opening="",
        closing="",
        main=None,
        css_classes=None,
        **attributes
    ):
        self.tag_name = tag_name
        self._opening = opening
        self._closing = closing

        if main:
            if main is True:  # Instead of just truthy
                self.main = get_dir_name()  # Use current directory's name
            else:
                self.main = str(main)
        else:
            self.main = ""

        self._id = ""

        self._src_folder = "assets"
        self._dst_folder = "static"

        self.children = list()
        self.attributes = dict()

        self._pre_html = ""

        self._append_head_no_nb_css = dict()
        self._append_head_no_nb_js = dict()

        self._pyviz_extensions = set()

        self._body_classes = set()

        self._prepend_body_css = dict()
        self._prepend_body_style = dict()

        self._component_data = dict()
        self.data_prefix = ""
        self.data_postfix = ""

        self._panel_css_files = dict()
        self._panel_raw_css = dict()

        self._panels = dict()
        self._no_panel_spacer = ""

        self._append_body_js = dict()
        self._append_body_script = dict()

        self._append_body_no_nb_js = dict()
        self._append_body_no_nb_script = dict()

        self._post_html = ""

        self._files_attrs = dict()
        self._files_uris = set()
        self._asset_folders = list()

        self.css_classes = set()
        if css_classes:
            if isinstance(css_classes, str):
                css_classes = css_classes.split()
            self.add_classes(*css_classes)

        if attributes:
            self.add_attributes(**attributes)

        if children:
            self.add_children(*children)

    @property
    def id(self):
        if not self._id:
            # Auto-generate an unique id for the component
            self.id = "id" + str(uuid.uuid4().hex)
        return self._id

    @id.setter
    def id(self, value):
        self._id = value
        self.attributes["id"] = self._id

    def add_classes(self, *css_classes):
        css_classes_set = set(css_classes)
        css_classes_set.discard("")
        css_classes_set.discard(None)
        self.css_classes = self.css_classes.union(css_classes_set)
        return self

    def add_attributes(self, **attributes):

        if attributes:
            if "class" in attributes:
                self.add_classes(attributes["class"])
                del attributes["class"]

        for attr in attributes:
            attr_value = attributes[attr]
            if attr_value is True:
                attr_value = "true"
            elif attr_value is False:
                attr_value = "false"
            elif isinstance(attr_value, str):
                if (
                    attr in ["href", "src"]
                    or self.tag_name == "object"
                    and attr == "data"
                ):
                    attr_value = attr_value.strip()
                    attr_schema = attr_value.lower()[:6]
                    if not (
                        attr_schema in ["https:", "http:/"]
                        or attr_schema.startswith("//")
                    ):
                        attr_url = urlsplit(attr_value).geturl()
                        if attr_url:
                            self._files_attrs[attr] = attr_url
                            if can_make_inline_uri(attr_url):
                                self._files_uris.add(attr_value)
                else:
                    attr_value = html.escape(attr_value)
            elif is_a_number(attr_value):
                attr_value = str(attr_value)
            else:
                attr_value = None
            if attr_value is not None:
                attr = attr.replace("_", "-")
                self.attributes[attr] = attr_value

        if "id" in self.attributes:
            self.id = attributes["id"]

        return self

    def append_head_no_nb_css(self, **files):
        self._append_head_no_nb_css.update(files)
        return self

    def get_append_head_no_nb_css(self):
        append_head_no_nb_css = self._append_head_no_nb_css.copy()
        for child in self.children:
            append_head_no_nb_css.update(child.get_append_head_no_nb_css())
        return append_head_no_nb_css

    def append_head_no_nb_js(self, **files):
        self._append_head_no_nb_js.update(files)
        return self

    def get_append_head_no_nb_js(self):
        append_head_no_nb_js = self._append_head_no_nb_js.copy()
        for child in self.children:
            append_head_no_nb_js.update(child.get_append_head_no_nb_js())
        return append_head_no_nb_js

    def pyviz_extensions(self, *extensions):
        extensions_no_spaces = [item.split() for item in extensions if item]
        self._pyviz_extensions = self._pyviz_extensions.union(
            set(itertools.chain.from_iterable(extensions_no_spaces))
        )
        return self

    def get_pyviz_extensions(self):
        pyviz_extensions = self._pyviz_extensions.copy()
        for child in self.children:
            pyviz_extensions = pyviz_extensions.union(child.get_pyviz_extensions())
        return pyviz_extensions

    def body_classes(self, *classes):
        classes_no_spaces = [item.split() for item in classes if item]
        self._body_classes = self._body_classes.union(
            set(itertools.chain.from_iterable(classes_no_spaces))
        )
        return self

    def get_body_classes(self):
        body_classes = self._body_classes.copy()
        for child in self.children:
            body_classes = body_classes.union(child.get_body_classes())
        return body_classes

    def prepend_body_css(self, **files):
        self._prepend_body_css.update(files)
        return self

    def get_prepend_body_css(self):
        prepend_body_css = self._prepend_body_css.copy()
        for child in self.children:
            prepend_body_css = dict(child.get_prepend_body_css(), **prepend_body_css)
        return prepend_body_css

    def prepend_body_style(self, **styles):
        self._prepend_body_style.update(styles)
        return self

    def get_prepend_body_style(self):
        prepend_body_style = self._prepend_body_style.copy()
        for child in self.children:
            prepend_body_style = dict(
                child.get_prepend_body_style(), **prepend_body_style
            )
        return prepend_body_style

    def component_data(self, prefix=None, data=None, postfix=None):
        if self.id not in self._component_data:
            self._component_data[self.id] = {
                "prefix": prefix,
                "data": data,
                "postfix": postfix,
            }
        else:
            if prefix is not None:
                self._component_data[self.id]["refix"] = prefix
            if data is not None:
                self._component_data[self.id]["data"] = data
            if postfix is not None:
                self._component_data[self.id]["postfix"] = postfix
        return self

    def data(self, data):
        self.component_data(data=data)
        return self

    def get_component_data(self):
        component_data = self._component_data.copy()
        for child in self.children:
            component_data.update(child.get_component_data())
        return component_data

    def get_data_prefix(self):
        data_prefix = self.data_prefix
        if not data_prefix:
            for child in self.children:
                data_prefix = child.get_data_prefix()
                if data_prefix:
                    break
        return data_prefix

    def get_data_postfix(self):
        data_postfix = self.data_postfix
        if not data_postfix:
            for child in self.children:
                data_postfix = child.get_data_postfix()
                if data_postfix:
                    break
        return data_postfix

    def panel_css_files(self, **files):
        self._panel_css_files.update(files)
        return self

    def get_panel_css_files(self):
        panel_css_files = self._panel_css_files.copy()
        for child in self.children:
            panel_css_files.update(child.get_panel_css_files())
        return panel_css_files

    def panel_raw_css(self, **styles):
        self._panel_raw_css.update(styles)
        return self

    def get_panel_raw_css(self):
        panel_raw_css = self._panel_raw_css.copy()
        for child in self.children:
            panel_raw_css.update(child.get_panel_raw_css())
        return panel_raw_css

    def append_body_js(self, **files):
        self._append_body_js.update(files)
        return self

    def get_append_body_js(self):
        append_body_js = self._append_body_js.copy()
        for child in self.children:
            append_body_js.update(child.get_append_body_js())
        return append_body_js

    def append_body_script(self, **scripts):
        self._append_body_script.update(scripts)
        return self

    def get_append_body_script(self):
        append_body_script = self._append_body_script.copy()
        for child in self.children:
            append_body_script.update(child.get_append_body_script())
        return append_body_script

    def append_body_no_nb_js(self, **files):
        self._append_body_no_nb_js.update(files)
        return self

    def get_append_body_no_nb_js(self):
        append_body_no_nb_js = self._append_body_no_nb_js.copy()
        for child in self.children:
            append_body_no_nb_js.update(child.get_append_body_no_nb_js())
        return append_body_no_nb_js

    def append_body_no_nb_script(self, **scripts):
        self._append_body_no_nb_script.update(scripts)
        return self

    def get_append_body_no_nb_script(self):
        append_body_no_nb_script = self._append_body_no_nb_script.copy()
        for child in self.children:
            append_body_no_nb_script.update(child.get_append_body_no_nb_script())
        return append_body_no_nb_script

    def files_uris(self, *files):
        for filename in files:
            self._files_uris.add(filename.strip())
        return self

    def get_files_uris(self):
        files_uris = self._files_uris.copy()
        for child in self.children:
            files_uris = files_uris.union(child.get_files_uris())
        return files_uris

    def asset_folders(self, *folders):
        for folder in folders:
            self._asset_folders.append(folder.strip())
        return self

    def get_asset_folders(self):
        asset_folders = self._asset_folders.copy()
        for child in self.children:
            asset_folders = child.get_asset_folders() + asset_folders
        return asset_folders

    def opening(self, markup):
        self._opening += markup
        return self

    def prepend_html(self, markup):
        self._pre_html += template_escape(markup)
        return self

    def _append_html_child(self, child):
        child_component = Component()
        child_component.append_html(html.escape(child))
        self.children.append(child_component)
        return self

    def _append_panel_child(self, child):
        child_id = "panel_" + str(uuid.uuid4().hex)
        child_component = Component()
        self._post_html += r"{{ embed(roots." + child_id + r") }}"
        self.children.append(child_component)
        self._panels[child_id] = child
        return self

    def add_children(self, *args):
        if args:
            for child in args:
                if isinstance(child, tuple):
                    for sub_child in child:
                        if sub_child is not None:
                            if isinstance(sub_child, Component):
                                self.children.append(sub_child)
                            elif isinstance(sub_child, str):
                                self._append_html_child(sub_child)
                            elif is_a_number(sub_child):
                                self._append_html_child(str(sub_child))
                            else:
                                self._append_panel_child(sub_child)
                elif isinstance(child, Component):
                    self.children.append(child)
                elif isinstance(child, str):
                    self._append_html_child(child)
                elif is_a_number(child):
                    self._append_html_child(str(child))
                elif child:
                    self._append_panel_child(child)
        return self

    def append_html(self, markup):
        self._post_html = template_escape(markup) + self._post_html
        return self

    def closing(self, markup):
        self._closing += markup
        return self

    def get_attributes(self, main, asset_folders, nb=IS_A_JUPYTER_NOTEBOOK):
        attributes = ""
        for attr in self.attributes:
            attr_value = self.attributes[attr]

            if attr in self._files_attrs:
                if main:
                    self.files_uris(attr_value)
                if not main or nb:
                    if attr_value.startswith("?") and nb:
                        attr_value = None
                    elif attr_value in self._files_uris:
                        attr_url = urlsplit(attr_value).geturl()
                        if attr_url:
                            uri_value = make_inline_uri(
                                attr_url,
                                self._src_folder,
                                self._dst_folder,
                                asset_folders=asset_folders,
                            )
                            if uri_value:
                                attr_value = uri_value
                else:
                    if len(attr_value) is not 0 and attr == "src":
                        attr_value = "{}/{}/{}".format(
                            main, self._dst_folder, attr_value
                        )
                    elif len(attr_value) is 0:
                        attributes += " {}".format(attr)
                    else:
                        attributes += ' {}="{}"'.format(attr, attr_value)

            if attr_value is not None:
                if len(attr_value) is 0:
                    attributes += " {}".format(attr)
                else:
                    attributes += ' {}="{}"'.format(attr, attr_value)

        if self.css_classes:
            attributes += ' class="{}"'.format(html.escape(" ".join(self.css_classes)))
        return attributes

    def get_panels(self):
        panels = self._panels.copy()
        for child in self.children:
            panels.update(child.get_panels())
        return panels

    def extension(self, *args, **params):
        pn.extension(*args, **params)
        for name in args:
            if isinstance(name, str) and name in PYVIZ_EXTENSIONS:
                self._pyviz_extensions.add(name)
        return self

    def _make_available_head_no_nb(self, asset_folders):
        append_head_no_nb_js = self.get_append_head_no_nb_js()
        for item_name in append_head_no_nb_js:
            item = append_head_no_nb_js[item_name]
            make_available(
                item,
                src_folder=self._src_folder,
                dst_folder=self._dst_folder,
                asset_folders=asset_folders,
            )
        append_head_no_nb_css = self.get_append_head_no_nb_css()
        for item_name in append_head_no_nb_css:
            item = append_head_no_nb_css[item_name]
            make_available(
                item,
                src_folder=self._src_folder,
                dst_folder=self._dst_folder,
                asset_folders=asset_folders,
            )

    def _get_template_head_no_nb(self, asset_folders):
        template = ""
        append_head_no_nb_js = self.get_append_head_no_nb_js()
        for item_name in append_head_no_nb_js:
            item = append_head_no_nb_js[item_name]
            if self.main:
                template += """
<script src="/{}/{}/{}" type="text/javascript" crossorigin="anonymous"></script>""".format(
                    self.main, self._dst_folder, item
                )
            else:
                template += (
                    """
<script type="text/javascript">
"""
                    + get_inline_js(
                        item, src_folder=self._src_folder, asset_folders=asset_folders,
                    )
                    + "</script>"
                )

        append_head_no_nb_css = self.get_append_head_no_nb_css()
        for item_name in append_head_no_nb_css:
            item = append_head_no_nb_css[item_name]
            if self.main:
                template += """
<link href="/{}/{}/{}" rel="stylesheet" crossorigin="anonymous">""".format(
                    self.main, self._dst_folder, item
                )
            else:
                template += (
                    """
<style>
"""
                    + get_inline_css(
                        item, src_folder=self._src_folder, asset_folders=asset_folders,
                    )
                    + "</style>"
                )
        return template

    def _make_available_head_resources(self, asset_folders):
        pyviz_extensions = self.get_pyviz_extensions().union({"bokeh"})

        for extension_name in pyviz_extensions:
            extension = PYVIZ_EXTENSIONS[extension_name]

            if "css" in extension:
                # TODO add support for CDN resources
                if "local" in extension["css"]:
                    for item in extension["css"]["local"]:
                        make_available(
                            item,
                            src_folder=self._src_folder,
                            dst_folder=self._dst_folder,
                            asset_folders=asset_folders,
                        )
            if "js" in extension:
                # TODO add support for CDN resources
                if "local" in extension["js"]:
                    for item in extension["js"]["local"]:
                        make_available(
                            item,
                            src_folder=self._src_folder,
                            dst_folder=self._dst_folder,
                            asset_folders=asset_folders,
                        )

    def _get_template_pyviz_resources(self, asset_folders):
        template = ""
        pyviz_extensions = self.get_pyviz_extensions().union({"bokeh"})

        for extension_name in pyviz_extensions:
            extension = PYVIZ_EXTENSIONS[extension_name]

            if "css" in extension:
                # TODO add support for CDN resources
                if "local" in extension["css"]:
                    for item in extension["css"]["local"]:
                        if self.main:
                            template += """
<link href="/{}/{}/{}" rel="stylesheet" crossorigin="anonymous">""".format(
                                self.main, self._dst_folder, item
                            )
                        else:
                            template += (
                                """
<style>
"""
                                + get_inline_css(
                                    item,
                                    src_folder=self._src_folder,
                                    asset_folders=asset_folders,
                                )
                                + "</style>"
                            )

            if "js" in extension:
                # TODO add support for CDN resources
                if "local" in extension["js"]:
                    for item in extension["js"]["local"]:
                        if self.main:
                            template += """
<script src="/{}/{}/{}" type="text/javascript" crossorigin="anonymous"></script>""".format(
                                self.main, self._dst_folder, item
                            )
                        else:
                            template += (
                                """
<script type="text/javascript">
"""
                                + get_inline_js(
                                    item,
                                    src_folder=self._src_folder,
                                    asset_folders=asset_folders,
                                )
                                + "</script>"
                            )
        return template

    def _get_template_body_classes_attr(self):
        classes = self.get_body_classes()
        if classes:
            return ' class="' + " ".join(classes) + '"'
        else:
            return ""

    def _get_template_contents_top(self, asset_folders, nb=IS_A_JUPYTER_NOTEBOOK):
        template = ""
        prepend_body_css = self.get_prepend_body_css()
        for item_name in prepend_body_css:
            item = prepend_body_css[item_name]
            if self.main:
                make_available(
                    item,
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders,
                )
            if self.main and not nb:
                template += """
<link href="/{}/{}/{}" rel="stylesheet" crossorigin="anonymous">""".format(
                    self.main, self._dst_folder, item
                )
            else:
                template += (
                    """
<style>
"""
                    + get_inline_css(
                        item, src_folder=self._src_folder, asset_folders=asset_folders,
                    )
                    + "</style>"
                )

        prepend_body_style = self.get_prepend_body_style()
        for item_name in prepend_body_style:
            template += (
                """
<style>
"""
                + prepend_body_style[item_name].replace("</style", r"\00003c/style")
                + "</style>"
            )
        return template

    def _make_available_contents_bottom_no_nb(self, asset_folders):
        append_body_no_nb_js = self.get_append_body_no_nb_js()
        for item_name in append_body_no_nb_js:
            item = append_body_no_nb_js[item_name]
            make_available(
                item,
                src_folder=self._src_folder,
                dst_folder=self._dst_folder,
                asset_folders=asset_folders,
            )

    def _get_template_contents_bottom_no_nb(self, asset_folders):
        template = ""
        append_body_no_nb_js = self.get_append_body_no_nb_js()
        for item_name in append_body_no_nb_js:
            item = append_body_no_nb_js[item_name]
            if self.main:
                template += """
<script src="/{}/{}/{}" type="text/javascript" crossorigin="anonymous"></script>""".format(
                    self.main, self._dst_folder, item
                )
            else:
                template += (
                    """
<script type="text/javascript">
"""
                    + get_inline_js(
                        item, src_folder=self._src_folder, asset_folders=asset_folders,
                    )
                    + "</script>"
                )

        append_body_no_nb_script = self.get_append_body_no_nb_script()
        for item_name in append_body_no_nb_script:
            item = append_body_no_nb_script[item_name]
            template += (
                """
<script type="text/javascript">
"""
                + get_inline_js(
                    item, src_folder=self._src_folder, asset_folders=asset_folders,
                )
                + "</script>"
            )
        return template

    def get_data_template(self):
        template = ""

        data = self.get_component_data()
        data_value_elements = list()
        data_elements = list()

        for component_id in data:
            item = data[component_id]

            try:
                json_data = json.dumps(item["data"])
                data_value_elements.append(component_id + ": " + json_data)
            except:
                pass

            if isinstance(item["data"], Component):
                data_value_id = item["data"].id
            else:
                data_value_id = component_id
            item_elements = [
                item["prefix"],
                'data: window.data_values["' + data_value_id + '"]',
                item["postfix"],
            ]
            data_elements.append(
                component_id
                + """: {
      """
                + """,
      """.join(
                    filter(None, item_elements)
                )
                + """
    }"""
            )

        if data_value_elements:
            data_script = (
                """
window.data_values = {
    """
                + """,
      """.join(
                    data_value_elements
                )
                + """
}"""
            ).replace("</script", r"\u003c/script")
        else:
            data_script = ""

        data_prefix = self.get_data_prefix()
        data_postfix = self.get_data_postfix()

        if data_elements or data_prefix or data_postfix:
            if not data_prefix:
                data_prefix = """
window.data = {
    """
            if not data_postfix:
                data_postfix = """
}"""
            custom_data_script = (
                data_prefix
                + """,
    """.join(
                    data_elements
                )
                + data_postfix
            ).replace("</script", r"\u003c/script")
        else:
            custom_data_script = ""

        template += (
            """
<script type="text/javascript">
"""
            + data_script
            + """
"""
            + custom_data_script
            + """
</script>"""
        )
        return template

    def _get_template_contents_bottom(self, asset_folders, nb=IS_A_JUPYTER_NOTEBOOK):
        template = ""
        append_body_js = self.get_append_body_js()
        for item_name in append_body_js:
            item = append_body_js[item_name]
            if self.main:
                make_available(
                    item,
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders,
                )
            if self.main and not nb:
                template += """
<script src="/{}/{}/{}" type="text/javascript" crossorigin="anonymous"></script>""".format(
                    self.main, self._dst_folder, item
                )
            else:
                template += (
                    """
<script type="text/javascript">
"""
                    + get_inline_js(
                        item, src_folder=self._src_folder, asset_folders=asset_folders,
                    )
                    + "</script>"
                )

        append_body_script = self.get_append_body_script()
        for item_name in append_body_script:
            template += (
                """
<script type="text/javascript">
"""
                + append_body_script[item_name].replace("</script", r"\u003c/script")
                + "</script>"
            )

        template += self.get_data_template()

        return template

    def _get_template(self, asset_folders):
        if self.main:
            self._make_available_head_resources(asset_folders)
            self._make_available_head_no_nb(asset_folders)
            self._make_available_contents_bottom_no_nb(asset_folders)
        return (
            """\
{% extends base %}

{% block head %}
<head>
    {% block inner_head %}
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{% block title %}{{ title | e if title else "Panel App" }}{% endblock %}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {% block preamble %}{% endblock %}
    {% block resources %}
"""
            + template_escape(self._get_template_pyviz_resources(asset_folders))
            + """
    {% endblock %}
    {% block postamble %}
"""
            + template_escape(self._get_template_head_no_nb(asset_folders))
            + """
    {% endblock %}
    {% endblock %}
</head>
{% endblock %}

{% block body %}
<body"""
            + template_escape(self._get_template_body_classes_attr())
            + """>
"""
            + template_escape(
                self._get_template_contents_top(asset_folders=asset_folders, nb=False)
            )
            + """
    {% block inner_body %}
    {% block contents %}
"""
            + self.get_html(self.main, asset_folders=asset_folders, nb=False)
            + self._no_panel_spacer
            + """
    {% endblock %}
    {{ plot_script | indent(8) }}
"""
            + template_escape(
                self._get_template_contents_bottom(
                    asset_folders=asset_folders, nb=False
                )
            )
            + template_escape(self._get_template_contents_bottom_no_nb(asset_folders))
            + """
    {% endblock %}
</body>
{% endblock %}
"""
        )

    def _get_nb_template(self, asset_folders, nb=IS_A_JUPYTER_NOTEBOOK):
        return (
            """\
{% extends base %}

{% block contents %}
"""
            + template_escape(
                self._get_template_contents_top(asset_folders=asset_folders, nb=nb)
            )
            + self.get_html(self.main, asset_folders=asset_folders)
            + self._no_panel_spacer
            + template_escape(
                self._get_template_contents_bottom(asset_folders=asset_folders, nb=nb)
            )
            + """
{% endblock %}
"""
        )

    def servable(self, *args, **kwargs):
        asset_folders = self.get_asset_folders()
        for filename in self.get_files_uris():
            if self.main:
                make_available(
                    filename,
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders,
                )
        self._no_panel_spacer = ""
        panels = self.get_panels()
        if not panels:
            pn.extension()
            child_id = "panel_" + str(uuid.uuid4().hex)
            self._no_panel_spacer = r"{{ embed(roots." + child_id + r") }}"
            panels[child_id] = pn.Spacer()

        tmpl = pn.Template(
            self._get_template(asset_folders),
            nb_template=self._get_nb_template(asset_folders),
        )
        for panel in panels:
            tmpl.add_panel(panel, panels[panel])

        panel_css_files = self.get_panel_css_files()
        if panel_css_files:
            pn.extension(css_files=list(panel_css_files.values()))

        panel_raw_css = self.get_panel_raw_css()
        if panel_raw_css:
            pn.extension(raw_css=list(panel_raw_css.values()))

        tmpl.servable(*args, **kwargs)
        return tmpl

    def get_html(self, main, asset_folders=None, nb=IS_A_JUPYTER_NOTEBOOK):
        if asset_folders is None:
            asset_folders = self.get_asset_folders()

        opening = self._opening
        if opening.endswith("/>"):
            opening_close = "/>"
            opening = opening[:-2]
        else:
            if opening.endswith(">"):
                opening_close = ">"
                opening = opening[:-1]
            elif opening:
                opening_close = ">"
            else:
                opening_close = ""
        closing = self._post_html + self._closing

        if opening:
            opening += (
                self.get_attributes(main, asset_folders=asset_folders, nb=nb)
                + opening_close
            )

        markup = opening + self._pre_html

        for child in self.children:
            markup += child.get_html(main, asset_folders)

        markup += closing

        return markup

    def _repr_html_(self, asset_folders=None, nb=IS_A_JUPYTER_NOTEBOOK):
        if asset_folders is None:
            asset_folders = self.get_asset_folders()
        return (
            self._get_template_contents_top(asset_folders=asset_folders, nb=nb)
            + """ 
"""
            + self.get_html(self.main, asset_folders)
            + """ 
"""
            + self._get_template_contents_bottom(asset_folders=asset_folders, nb=nb)
        )

