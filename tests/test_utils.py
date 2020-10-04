# pylint: disable=redefined-outer-name,protected-access
# pylint: disable=missing-function-docstring,missing-module-docstring,missing-class-docstring
import os
import pathlib

import pytest
from panel_components.utils import (
    IS_A_JUPYTER_NOTEBOOK,
    _read_file,
    find_src_file,
    get_dir_name,
    is_a_number,
    template_escape,
    get_inline_js,
    get_inline_css,
    make_available,
    can_make_inline_uri,
    make_inline_uri,
)


@pytest.fixture
def src_folder_path(tmp_path):
    path = tmp_path / "src"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def src_folder(src_folder_path):
    return str(src_folder_path)


@pytest.fixture
def filename():
    return "image.png"


@pytest.fixture
def src_file_text():
    return "src"


@pytest.fixture()
def src_file_path(src_folder_path, filename, src_file_text):
    path = src_folder_path / filename
    path.write_text(src_file_text)
    return path


@pytest.fixture()
def src_file(src_file_path):
    return str(src_file_path)


def test_is_a_jupyter_notebook():
    assert not IS_A_JUPYTER_NOTEBOOK


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        (0, True),
        (1, True),
        (1.1, True),
        ("test", False),
        (is_a_number, False),
        (pytest, False),
    ],
)
def test_is_a_number(value, expected):
    assert is_a_number(value) is expected


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        ("{{ value }}", "{{'{{'}} value }}"),
        ("{% value }", "{{'{%'}} value }"),
        ("{# value }", "{{'{#'}} value }"),
    ],
)
def test_template_escape(value, expected):
    assert template_escape(value) == expected


@pytest.mark.parametrize(
    ["folder", "expected"],
    [
        (None, "panel-components"),
        ("/c/repos/panel-components", "panel-components"),
        ("/c/repos/panel-components/", "panel-components"),
    ],
)
def test_get_dir_name(folder, expected):
    assert get_dir_name(folder) == expected


def test_read_file_none():
    assert _read_file(None) == ""


def test_read_file_not_a_file():
    assert _read_file("this.file.does.not.exist") == ""


def test_read_file_when_a_directory():
    assert _read_file(os.getcwd()) == ""


def test_read_file(tmp_path: pathlib.Path):
    # When
    file = tmp_path / "tmp.txt"
    file.write_text("hello world")
    # Then
    assert _read_file(str(file)) == "hello world"


def test_find_src_file(filename, src_folder, src_file):
    # When
    src, dst = find_src_file(filename=filename, src_folder=src_folder)

    # Then
    assert src == src_file
    assert dst is None


def test_find_asset_file(tmp_path: pathlib.Path, src_folder):
    # Given
    filename = "image.png"

    asset_folder_path = tmp_path / "asset"
    asset_folder_path.mkdir(parents=True, exist_ok=True)
    asset_folder = str(asset_folder_path)

    asset_file_path = asset_folder_path / filename
    asset_file_path.write_text("asset")
    asset_file = str(asset_file_path)

    # When
    src, dst = find_src_file(
        filename=filename, src_folder=src_folder, dst_folder=None, asset_folders=[asset_folder]
    )

    # Then
    assert src == asset_file
    assert dst is None


def test_find_dst_file(tmp_path: pathlib.Path):
    # Given
    filename = "image.png"

    src_folder_path = tmp_path / "src"
    src_folder_path.mkdir(parents=True, exist_ok=True)
    src_folder = str(src_folder_path)

    dst_folder_path = tmp_path / "dst"
    dst_folder_path.mkdir(parents=True, exist_ok=True)
    dst_folder = str(dst_folder_path)
    dst_file_path = dst_folder_path / filename
    dst_file_path.write_text("dst")
    dst_file = str(dst_file_path)

    # When
    src, dst = find_src_file(filename=filename, src_folder=src_folder, dst_folder=dst_folder)

    # Then
    assert src is None
    assert dst == dst_file


def test_get_inline_js(filename, src_folder, src_file_path):
    src_file_path.write_text("<script>var a=1</script>")
    assert get_inline_js(filename, src_folder) == "<script>var a=1\\u003c/script>"


def test_get_inline_css(filename, src_folder, src_file_path):
    src_file_path.write_text("<style>body {background: text}</style>")
    assert get_inline_css(filename, src_folder) == "<style>body {background: text}\\00003c/style>"


def test_make_available(filename, src_folder, src_file, tmp_path): # pylint: disable=unused-argument
    dst_path = tmp_path / "desty"
    dst_folder = str(dst_path)
    dst_file = dst_path / filename
    # When
    make_available(filename=filename, src_folder=src_folder, dst_folder=dst_folder)
    # Then
    assert dst_file.exists()


@pytest.mark.parametrize(
    ["file", "expected"],
    [
        ("image.png", True),
        ("/c/image.png", True),
        ("/c/image.png ", True),
        ("/www/image.gif", True),
        ("/www/image.jpg", True),
        ("/www/image.jpeg", True),
        ("/www/image.svg", True),
        ("/www/font.ttf", True),
        ("/www/font.otf", True),
        ("/www/font.woff", True),
        ("/www/font.woff2", True),
        ("/www/font.eot", True),
        ("/www/test.py", False),
    ],
)
def test_can_make_inline_uri(file, expected):
    assert can_make_inline_uri(file) is expected


@pytest.mark.parametrize(
    ["file", "inline_uri_start"],
    [
        (
            "cubes-solid.svg",
            'data:image/svg+xml;charset=utf8,&lt;svg aria-hidden=&quot;true&quot; focusable=&quot;false&quot; data-prefix=&quot;fas&quot; data-icon=&quot;cubes&quot; class=&quot;svg-inline--fa fa-cubes fa-w-16&quot; role=&quot;img&quot; xmlns=&quot;http://www.w3.org/2000/svg&quot; viewBox=&quot;0 0 512 512&quot;&gt;&lt;path fill=&quot;currentColor&quot; d=&quot;M488.6 250.2L392 214V105.5c0-15-9.3-28.4-23.4-33.7l-100-37.5c-8.1-3.1-17.1-3.1-25.3 0l-100 37.5c-14.1 5.3-23.4 18.7-23.4 33.7V214l-96.6 36.2C9.3 255.5 0 268.9 0 283.9V394c0 13.6 7.7 26.1 19.9 32.2l100 50c10.1 5.1 22.1 5.1 32.2 0l103.9-52 103.9 52c10.1 5.1 22.1 5.1 32.2 0l100-50c12.2-6.1 19.9-18.6 19.9-32.2V283.9c0-15-9.3-28.4-23.4-33.7zM358 214.8l-85 31.9v-68.2l85-37v73.3zM154 104.1l102-38.2 102 38.2v.6l-102 41.4-102-41.4v-.6zm84 291.1l-85 42.5v-79.1l85-38.8v75.4zm0-112l-102 41.4-102-41.4v-.6l102-38.2 102 38.2v.6zm240 112l-85 42.5v-79.1l85-38.8v75.4zm0-112l-102 41.4-102-41.4v-.6l102-38.2 102 38.2v.6z&quot;&gt;&lt;/path&gt;&lt;/svg&gt;") format("svg");', # pylint: disable=line-too-long
        ),
        ("awesome-panel-extensions.png", "data:image/png;charset=utf8;base64,iVBORw0KG"),
        ("kickstarter.gif", "data:image/gif;charset=utf8;base64,R0lGOD"),
        ("panel_index.jpg", "data:image/jpeg;charset=utf8;base64,/9j/4AAQS"),
        ("detr.jpeg", "data:image/jpeg;charset=utf8;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEB"),
        ("fontawesome-webfont.ttf", "data:application/x-font-ttf;charset=utf8;base64,AAEAAAAOAI"),
        ("FontAwesome.otf", "data:application/x-font-otf;charset=utf8;base64,T1RUTwA"),
        ("fontawesome-webfont.woff", "data:application/x-font-woff;charset=utf8;base64,d09GRg"),
        ("wired.woff2", "data:application/x-font-woff2;charset=utf8;base64,d09GMgAB"),
        ("fontawesome-webfont.eot", "data:application/x-font-eot;charset=utf8;base64,5ioBAAAqA"),
    ],
)
def test_make_inline_uri(file, inline_uri_start):
    src_folder = str(pathlib.Path(__file__).parent / "fixtures/")
    assert inline_uri_start in make_inline_uri(src_file=file, src_folder=src_folder)
