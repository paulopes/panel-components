"""The purpose of this module is to test the TemporaryResources context manager

The purpose of the TemporaryResources context manager is to enable using temporary, specific
configuration of resources when creating a custom Template.

If you use the global configuration `pn.config` for your templates you will include the same
css and js files in all templates. This is problematic if you want different templates, like for
example a light template, a dark template, a bootstrap template, a material template, a template
with Plotly Plots, a template without Plotly plots etc.
"""
import panel as pn
import pytest
from panel_components.resources import TemporaryResources
# pylint: disable=missing-function-docstring

@pytest.fixture(scope="function", autouse=True)
def clear_config_except_panel_css():
    """Reset pn.config except for panel css"""
    # pylint: disable=protected-access
    pn.config.raw_css = []
    pn.config.js_files = {}
    pn.config.css_files = [
        file for file in pn.config.css_files if TemporaryResources._is_panel_style_file(file)
    ]


@pytest.fixture()
def clear_config():
    """Reset pn.config"""
    pn.config.raw_css = []
    pn.config.js_files = {}
    pn.config.css_files = []


def _contains_bokeh_and_panel_resources(text):
    return (
        "bokeh-" in text
        and "bokeh-widgets" in text
        and "bokeh-tables" in text
        and ".panel-widget-box"
    )


def test_does_not_include_pn_config_raw_css():
    # Given
    pre_raw_css = "body {background: black;"

    # When
    pn.config.raw_css.append(pre_raw_css)
    backup = pn.config.raw_css

    with TemporaryResources():
        text = pn.io.resources.Resources().render()

    # Then
    assert pre_raw_css not in text
    assert pn.config.raw_css == backup
    assert _contains_bokeh_and_panel_resources(text)


def test_does_not_include_pn_config_css_files():
    # Given
    pre_css_file = "https://somedomain.com/test.css"

    # When
    pn.config.css_files.append(pre_css_file)
    backup = pn.config.css_files
    with TemporaryResources():
        text = pn.io.resources.Resources().render()

    # Then
    assert pre_css_file not in text
    assert pn.config.css_files == backup
    assert _contains_bokeh_and_panel_resources(text)


def test_does_not_include_pn_config_js_files():
    # Given
    pre_js = "http://some/domain.com/test.js"

    # When
    pn.config.js_files = {"somejs": pre_js}
    backup = pn.config.js_files
    with TemporaryResources():
        text = pn.io.resources.Resources().render()

    # Then
    assert pre_js not in text
    assert pn.config.js_files == backup
    assert _contains_bokeh_and_panel_resources(text)


def test_does_not_include_pn_extension():
    # Given
    pre_extension = "plotly"

    # When
    pn.extension(pre_extension)
    with TemporaryResources():
        text = pn.io.resources.Resources().render()

    # Then
    assert pre_extension not in text
    assert _contains_bokeh_and_panel_resources(text)


def test_includes_template_extension():
    extension = "katex"

    with TemporaryResources(extensions={extension}):
        text = pn.io.resources.Resources().render()

    assert extension in text
    assert _contains_bokeh_and_panel_resources(text)


def test_includes_template_raw_css():
    raw_css = "body {background: black;"

    with TemporaryResources(raw_css=[raw_css]):
        text = pn.io.resources.Resources().render()

    assert raw_css in text
    assert _contains_bokeh_and_panel_resources(text)


def test_includes_template_css_files():
    css_file = "https://somedomain.com/test.css"

    with TemporaryResources(css_files=[css_file]):
        text = pn.io.resources.Resources().render()

    assert css_file in text
    assert _contains_bokeh_and_panel_resources(text)


def test_includes_template_js_files():
    js_file = "http://some/domain.com/test.js"

    with TemporaryResources(js_files={"somejs": js_file}):
        text = pn.io.resources.Resources().render()

    assert js_file in text
    assert _contains_bokeh_and_panel_resources(text)


def test_can_exclude_panel_css():
    with TemporaryResources(include_panel_css=False):
        text = pn.io.resources.Resources().render()

    assert ".panel-widget-box" not in text


def test_complex_use_case():
    # Given
    pre_raw_css = "body {background: black;"
    pre_css_file = "https://somedomain.com/test.css"
    pre_js = "http://some/domain.com/test.js"
    pre_extension = "plotly"

    extension = "katex"

    # When
    pn.extension(pre_extension)
    pn.config.raw_css.append(pre_raw_css)
    pn.config.css_files.append(pre_css_file)
    pn.config.js_files = {"somejs": pre_js}
    backup_css_files = pn.config.css_files

    with TemporaryResources(extensions={extension}, include_panel_css=False):
        text = pn.io.resources.Resources().render()

    # Then
    assert "bokeh-" in text
    assert "bokeh-widgets" in text
    assert "bokeh-tables" in text
    assert ".panel-widget-box" not in text
    assert extension in text

    assert pre_raw_css not in text
    assert pre_css_file not in text
    assert pre_js not in text
    assert pre_extension not in text

    assert pn.config.raw_css == [pre_raw_css]
    assert pn.config.js_files == {"somejs": pre_js}
    assert pn.config.css_files == backup_css_files
