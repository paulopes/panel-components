# -*- coding: utf-8 -*-
from __future__ import print_function, division

import html
import uuid
import itertools

import panel as pn

from .utils import (
    IS_A_JUPYTER_NOTEBOOK,
    is_a_number,
    get_dir_name,
    clean_path,
    get_inline_js,
    get_inline_css,
    make_available,
    make_inline_uri,
)

try:
    from urllib.parse import quote
except:
    from urllib import quote


class Component:
    """Encapsulates all the html content, css and js requirements, as well as
    methods that assist in creating and generating a template (or html partial)
    for a component of a page that will served by a Panel server."""
    def __init__(
        self,
        *children,
        tag_name=None,
        xml_closing_style=False,
        title=None,
        main=None,
        css_classes=None,
        **attributes
    ):
        self._tag_name = tag_name
        self._xml_closing_style = xml_closing_style

        if title:
            self.title = title
        else:
            self.title = ""

        if main:
            self.main = main
        else:
            self.main = ""

        self._src_folder = "assets"
        self._dst_folder = "static"

        self.children = list()
        self.attributes = dict()

        self._pre_html = ""

        self._append_head_no_nb_css = dict()
        self._append_head_no_nb_js = dict()

        self._body_classes = set()

        self._prepend_body_css = dict()
        self._prepend_body_style = dict()

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
            self.add_classes(*css_classes)

        if attributes:
            self.add_attributes(**attributes)
        #     if "class" in attributes:
        #         self.add_classes(attributes["class"])
        #         del attributes["class"]
        #     self.attributes.update(attributes)

        # for attr in self.attributes:
        #     attr_value = self.attributes[attr]
        #     attr = attr.replace("_", "-")
        #     if attr_value:
        #         if isinstance(attr_value, str):
        #             if attr in ["href", "src"]:
        #                 attr_value = attr_value.strip()
        #                 attr_schema = attr_value.lower()[:6]
        #                 if not (
        #                     attr_schema in ["https:", "http:/"]
        #                     or attr_schema.startswith("//")
        #                 ):
        #                     self._files_attrs[attr] = attr_value
        #                     if attr_value[0] not in ["#", "?"]:
        #                         self._files_uris.add(attr_value)
        #                 # attr_value = quote(attr_value)
        #             else:
        #                 attr_value = html.escape(attr_value)
        #         elif isinstance(attr_value, bool):
        #             attr_value = "" if attr_value else None
        #         elif is_a_number(attr_value):
        #             attr_value = str(attr_value)
        #         else:
        #             attr_value = None
        #         if attr_value is not None:
        #             self.attributes[attr] = attr_value
                    
        if main is True:  # Instead of just truthy
            main = get_dir_name()  # Use current directory's name
            
        if children:
            self.add_children(*children)

    def add_classes(self, *css_classes):
        css_classes_set = set()
        for css_class in css_classes:
            if isinstance(css_class, str):
                css_class = css_class.split()
            if css_class:
                css_classes_set = css_classes_set.union(
                    set(tuple(css_class))
                )
        css_classes_set.discard("")
        css_classes_set.discard(None)
        self.css_classes = self.css_classes.union(css_classes_set)
        return self

    def add_attributes(self, **attributes):
        if attributes:
            if "class" in attributes:
                self.add_classes(attributes["class"])
                del attributes["class"]
            self.attributes.update(attributes)
        
        for attr in self.attributes:
            attr_value = self.attributes[attr]
            attr = attr.replace("_", "-")
            if attr_value:
                if isinstance(attr_value, str):
                    if attr in ["href", "src"]:
                        attr_value = attr_value.strip()
                        attr_schema = attr_value.lower()[:6]
                        if not (
                            attr_schema in ["https:", "http:/"]
                            or attr_schema.startswith("//")
                        ):
                            self._files_attrs[attr] = attr_value
                            if attr_value[0] not in ["#", "?"]:
                                self._files_uris.add(attr_value)
                        # attr_value = quote(attr_value)
                    else:
                        attr_value = html.escape(attr_value)
                elif isinstance(attr_value, bool):
                    attr_value = "" if attr_value else None
                elif is_a_number(attr_value):
                    attr_value = str(attr_value)
                else:
                    attr_value = None
                if attr_value is not None:
                    self.attributes[attr] = attr_value

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

    def body_classes(self, *classes):
        classes_no_spaces = [item.split() for item in classes if item]
        self._body_classes = self._body_classes.union(
            set(itertools.chain.from_iterable(classes_no_spaces))
        )
        return self

    def prepend_body_css(self, **files):
        self._prepend_body_css.update(files)
        return self

    def get_prepend_body_css(self):
        prepend_body_css = self._prepend_body_css.copy()
        for child in self.children:
            prepend_body_css.update(child.get_prepend_body_css())
        return prepend_body_css

    def prepend_body_style(self, **styles):
        self._prepend_body_style.update(styles)
        return self

    def get_prepend_body_style(self):
        prepend_body_style = self._prepend_body_style.copy()
        for child in self.children:
            prepend_body_style.update(child.get_prepend_body_style())
        return prepend_body_style

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

    def prepend_html(self, markup):
        self._pre_html += markup
        return self

    def _append_html_child(self, child):
        child_component = Component()
        child_component.append_html(html.escape(child))
        self.children.append(child_component)
        return self

    def _append_panel_child(self, child):
        child_id = "panel_" + str(uuid.uuid4().hex)
        child_component = Component()
        child_component.append_html(r"{{ embed(roots." + child_id + r") }}")
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
        self._post_html += markup
        return self

    def get_attributes(self, main, asset_folders):
        attributes = ""
        for attr in self.attributes:
            attr_value = self.attributes[attr]

            if attr in self._files_attrs:
                if main:
                    self.files_uris(attr_value)
                if not main or IS_A_JUPYTER_NOTEBOOK:
                    attr_value = make_inline_uri(
                        attr_value,
                        self._src_folder,
                        self._dst_folder,
                        asset_folders=asset_folders
                    )
                else:
                    attr_value = quote(
                        "{}/{}/{}".format(main, self._dst_folder, attr_value)
                    )

            if attr_value is not None:
                if len(attr_value) == 0:
                    attributes += " {}".format(attr)
                else:
                    attributes += ' {}="{}"'.format(attr, attr_value)
                    
        if self.css_classes:
            attributes += ' class="{}"'.format(
                html.escape(" ".join(self.css_classes))
            )
        return attributes

    def get_panels(self):
        panels = self._panels.copy()
        for child in self.children:
            panels.update(child.get_panels())
        return panels

    def _get_template_head_no_nb(self, asset_folders):
        template = ""
        append_head_no_nb_js = self.get_append_head_no_nb_js()
        for item_name in append_head_no_nb_js:
            if self.main:
                make_available(
                    append_head_no_nb_js[item_name],
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders
                )
                template += """
<script src="/{}/{}/{}" type="text/javascript" crossorigin="anonymous"></script>""".format(
                    self.main, self._dst_folder, append_head_no_nb_js[item_name]
                )
            else:
                template += (
                    """
<script type="text/javascript">
"""
                    + get_inline_js(append_head_no_nb_js[item_name], self._dst_folder)
                    + "</script>"
                )

        append_head_no_nb_css = self.get_append_head_no_nb_css()
        for item_name in append_head_no_nb_css:
            if self.main:
                make_available(
                    append_head_no_nb_css[item_name],
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders
                )
            if self.main and not IS_A_JUPYTER_NOTEBOOK:
                template += """
<link href="/{}/{}/{}" rel="stylesheet" crossorigin="anonymous">""".format(
                    self.main, self._dst_folder, append_head_no_nb_css[item_name]
                )
            else:
                template += (
                    """
<style>
"""
                    + get_inline_css(append_head_no_nb_css[item_name], self._dst_folder)
                    + "</style>"
                )
        return template

    def _get_template_body_classes_attr(self):
        # classes = self.get_body_classes()
        if self._body_classes:
            return ' class="' + " ".join(self._body_classes) + '"'
        else:
            return ""

    def _get_template_contents_top(self, asset_folders):
        template = ""
        prepend_body_css = self.get_prepend_body_css()
        for item_name in prepend_body_css:
            if self.main:
                make_available(
                    prepend_body_css[item_name],
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders
                )
            if self.main and not IS_A_JUPYTER_NOTEBOOK:
                template += """
<link href="/{}/{}/{}" rel="stylesheet" crossorigin="anonymous">""".format(
                    self.main, self._dst_folder, prepend_body_css[item_name]
                )
            else:
                template += (
                    """
<style>
"""
                    + get_inline_css(prepend_body_css[item_name], self._dst_folder)
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

    def _get_template_contents_bottom_no_nb(self, asset_folders):
        template = ""
        append_body_no_nb_js = self.get_append_body_no_nb_js()
        for item_name in append_body_no_nb_js:
            if self.main:
                make_available(
                    append_body_no_nb_js[item_name],
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders
                )
                template += """
<script src="/{}/{}/{}" type="text/javascript" crossorigin="anonymous"></script>""".format(
                    self.main, self._dst_folder, append_body_no_nb_js[item_name]
                )
            else:
                template += (
                    """
<script type="text/javascript">
"""
                    + get_inline_js(append_body_no_nb_js[item_name], self._dst_folder)
                    + "</script>"
                )

        append_body_no_nb_script = self.get_append_body_no_nb_script()
        for item_name in append_body_no_nb_script:
            template += (
                """
<script type="text/javascript">
"""
                + get_inline_js(append_body_no_nb_script[item_name], self._dst_folder)
                + "</script>"
            )
        return template

    def _get_template_contents_bottom(self, asset_folders):
        template = ""
        append_body_js = self.get_append_body_js()
        for item_name in append_body_js:
            if self.main:
                make_available(
                    append_body_js[item_name],
                    src_folder=self._src_folder,
                    dst_folder=self._dst_folder,
                    asset_folders=asset_folders
                )
            if self.main and not IS_A_JUPYTER_NOTEBOOK:
                template += """
<script src="/{}/{}/{}" type="text/javascript" crossorigin="anonymous"></script>""".format(
                    self.main, self._dst_folder, append_body_js[item_name]
                )
            else:
                template += (
                    """
<script type="text/javascript">
"""
                    + get_inline_js(append_body_js[item_name], self._dst_folder)
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
        return template

    def _get_template(self, asset_folders):
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
        {% block css_resources %}
        {{ bokeh_css | indent(8) if bokeh_css }}
        {% endblock %}
        {% block js_resources %}
        {{ bokeh_js | indent(8) if bokeh_js }}
        {% endblock %}
    {% endblock %}
    {% block postamble %}
"""
            + self._get_template_head_no_nb(asset_folders)
            + """
    {% endblock %}
    {% endblock %}
</head>
{% endblock %}

{% block body %}
<body"""
            + self._get_template_body_classes_attr()
            + """>
"""
            + self._get_template_contents_top(asset_folders)
            + """
    {% block inner_body %}
    {% block contents %}
"""
            + self._repr_html_(asset_folders=asset_folders)
            + self._no_panel_spacer
            + """
    {% endblock %}
    {{ plot_script | indent(8) }}
"""
            + self._get_template_contents_bottom(asset_folders)
            + self._get_template_contents_bottom_no_nb(asset_folders)
            + """
    {% endblock %}
</body>
{% endblock %}
"""
        )

    def _get_nb_template(self, asset_folders):
        return (
            """\
{% extends base %}

{% block contents %}
"""
            + self._get_template_contents_top(asset_folders)
            + self._repr_html_(asset_folders=asset_folders)
            + self._no_panel_spacer
            + self._get_template_contents_bottom(asset_folders)
            + """
{% endblock %}
"""
        )

    def app(self):
        asset_folders = self.get_asset_folders()
        for filename in self.get_files_uris():
            make_available(
                filename,
                src_folder=self._src_folder,
                dst_folder=self._dst_folder,
                asset_folders=asset_folders
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

        tmpl.servable(title=self.title)
        return tmpl

    def get_html(self, main, asset_folders):
        tag_name = self._tag_name
        markup = ""
        if (
            not self._xml_closing_style
            or self.children
            or self._pre_html
            or self._post_html
        ):
            if tag_name:
                markup = """
<{}{}>""".format(
                    tag_name, self.get_attributes(main, asset_folders)
                )

            markup += self._pre_html

            for child in self.children:
                markup += child.get_html(main, asset_folders)

            markup += self._post_html

            if tag_name:
                markup += """
</{}>""".format(
                    tag_name
                )

        elif tag_name:
            markup = """
<{}{} />""".format(
                tag_name, self.get_attributes(main, asset_folders)
            )

        return markup

    def _repr_html_(self, asset_folders=None):
        if asset_folders is None:
            asset_folders = self.get_asset_folders()
        return self.get_html(self.main, asset_folders)
