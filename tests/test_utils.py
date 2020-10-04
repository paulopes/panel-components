import os
import pathlib

import pytest
from panel_components import file
from panel_components.utils import (
    IS_A_JUPYTER_NOTEBOOK,
    _read_file,
    find_src_file,
    get_dir_name,
    is_a_number,
    template_escape,
)


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
        (None, os.getcwd()),
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


def test_find_src_file(tmp_path: pathlib.Path):
    filename = "image.png"
    src_folder_path = tmp_path / "src"
    src_folder_path.mkdir(parents=True, exist_ok=True)
    src_folder = str(src_folder_path)

    src_file_path = src_folder_path / filename
    src_file_path.write_text("src")
    src_file = str(src_file_path)

    src, dst = find_src_file(filename=filename, src_folder=src_folder)
    assert src == src_file
    assert dst == None
