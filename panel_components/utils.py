# -*- coding: utf-8 -*-
from __future__ import division, print_function

import base64
import errno
import html
import os
import shutil
from typing import Any, List, Optional

try:
    # Detect if running inside a Jupyter notebook
    if "ipykernel" in str(get_ipython()):
        IS_A_JUPYTER_NOTEBOOK = True
    else:
        IS_A_JUPYTER_NOTEBOOK = False
except NameError:
    IS_A_JUPYTER_NOTEBOOK = False


def is_a_number(value: Any):
    """Returns True if the value is a number

    Examples:

    >>> is_a_number(1.1)
    True
    >>> is_a_number("hello world")
    False

    Args:
        x (Any): Any kind of value

    Returns:
        [bool]: True if the value is a number. Otherwise False
    """
    try:
        return bool(0 == value * 0)
    except:
        return False


# Todo: Explain why }} should not be escaped
def template_escape(text: str) -> str:
    """Returns the text escaped an ready for usage in a Jinja template

    Escapes {{, {% and {#

    Example

    >>> template_escape("{% value }")
    "{{'{%'}} value }"

    Args:
        text (str): The text to escape

    Returns:
        str: Escaped text
    """
    escaped_text = (
        text.replace("{{", "{{'{{'}}").replace("{%", "{{'{%'}}").replace("{#", "{{'{#'}}")
    )
    return escaped_text


# Todo:
# The terminology dir and folder is used synonomously in this module
# Consider renaming simplifying by renaming get_dir_name to get_folder_name
def get_dir_name(folder: Optional[str] = None) -> str:
    """Returns the last name of the folder

    Example:
    >>> get_dir_name("/c/repos/panel-components")
    'panel-components'

    Args:
        folder (Optional[str], optional): The name of the folder. If None the folder is set to the
            working folder. Defaults to None.

    Returns:
        [str]: The folder name
    """
    if not folder:
        folder = os.getcwd()
    return folder.replace("/", os.sep).rstrip(os.sep).split(os.sep)[-1]


# Todo: Consider renaming src_path to path or file_path as this is more specific
def _read_file(src_path: Optional[str] = None) -> str:
    """Returns the text content of the src_path if it is a file

    Args:
        src_path (Optional[str], optional): The path to the file. Defaults to None.

    Returns:
        str: The text content of the file
    """
    file_contents = ""
    if src_path and os.path.isfile(src_path):
        with open(src_path, encoding="utf8") as src_file:
            file_contents = src_file.read()

    return file_contents


# Todo:
# This function is very complicated and could benefit from a refactoring
# Consider refactoring into find_src_file, find_dst_filde and file_src_and_dst_file functions
def find_src_file(
    filename: str,
    src_folder: str,
    dst_folder: Optional[str] = None,
    asset_folders: Optional[List[str]] = None,
):
    filename = filename.strip()

    file_path_elements = [
        element
        for element in filename.rstrip("/").split("/")
        if len(element) > 0 and element[0] != "."
    ]

    if dst_folder is None:
        dst_file = None
    else:
        dst_folder = os.sep.join([dst_folder] + file_path_elements[:-1])
        dst_file = os.path.join(dst_folder, file_path_elements[-1])

        if not dst_file or not os.path.isfile(dst_file):

            if not os.path.exists(dst_folder):
                try:
                    os.makedirs(dst_folder)
                except OSError as e:  # Guard against race condition
                    if e.errno != errno.EEXIST:
                        raise

    src_file = os.path.join(src_folder, *file_path_elements)
    src_exists = False
    if src_file and os.path.isfile(src_file):
        src_exists = True
    elif asset_folders:
        for folder in reversed(asset_folders):
            folder_path_elements = [
                element
                for element in folder.rstrip("/").split("/")
                if len(element) > 0 and element[0] != "."
            ]
            if folder.startswith("/"):
                folder_path_elements[0] = "/" + folder_path_elements[0]
            src_file = os.path.join(*folder_path_elements, *file_path_elements)
            if src_file and os.path.isfile(src_file):
                src_exists = True
                break
    if src_exists:
        return src_file, dst_file
    else:
        return None, dst_file


def get_inline_js(filename, src_folder, dst_folder=None, asset_folders=None):
    src_file, _ = find_src_file(filename, src_folder, dst_folder, asset_folders)
    return _read_file(src_file).replace("</script", r"\u003c/script")


def get_inline_css(filename, src_folder, dst_folder=None, asset_folders=None):
    src_file, _ = find_src_file(filename, src_folder, dst_folder, asset_folders)
    return _read_file(src_file).replace("</style", r"\00003c/style")


def make_available(filename, src_folder, dst_folder, asset_folders):
    src_file, dst_file = find_src_file(filename, src_folder, dst_folder, asset_folders)
    if src_file and not os.path.exists(dst_file):
        if not os.path.exists(dst_folder):
            try:
                os.makedirs(dst_folder)
            except OSError as e:  # Guard against race condition
                if e.errno != errno.EEXIST:
                    raise
        shutil.copyfile(src_file, dst_file)


def can_make_inline_uri(src_file):
    file_format = src_file.rstrip().split(".")[-1].lower()
    return file_format in {
        "png",
        "gif",
        "jpg",
        "jpeg",
        "svg",
        "ttf",
        "otf",
        "woff",
        "woff2",
        "eot",
    }


def make_inline_uri(src_file, src_folder, dst_folder, asset_folders=None):
    src_file = src_file.strip()
    if src_file in make_inline_uri.memo:
        return make_inline_uri.memo[src_file]

    memo_key = src_file
    return_value = ""
    src_exists = False

    if src_file[0] in ["/", "~"]:
        if src_file and os.path.isfile(src_file):
            src_exists = True
    else:
        file_path_elements = [
            element
            for element in src_file.strip("/").split("/")
            if len(element) > 0 and element[0] != "."
        ]

        src_file = os.path.join(src_folder, *file_path_elements)
        if src_file and os.path.isfile(src_file):
            src_exists = True
        elif asset_folders:
            for folder in reversed(asset_folders):
                folder_path_elements = [
                    element
                    for element in folder.strip("/").split("/")
                    if len(element) > 0 and element[0] != "."
                ]
                if folder.startswith("/"):
                    folder_path_elements[0] = "/" + folder_path_elements[0]
                src_file = os.path.join(*folder_path_elements, *file_path_elements)
                if src_file and os.path.isfile(src_file):
                    src_exists = True
                    break

    if src_exists:
        if src_file.lower().endswith(".svg"):
            svg = open(src_file).read()
            start = svg.find("<svg")
            start = svg.find("<SVG") if start < 0 else start
            return_value = 'data:image/svg+xml;charset=utf8,{}") format("svg");'.format(
                html.escape(svg[start:])
            )
        else:
            file_format = src_file.split(".")[-1].lower()
            if file_format == "jpg":
                file_format = "jpeg"
            if file_format in {"png", "gif", "jpeg"}:
                uri_start = "data:image/{};charset=utf8;base64,".format(file_format)
            elif file_format in {"ttf", "otf", "woff", "woff2", "eot"}:
                uri_start = "data:application/x-font-{};charset=utf8;base64,".format(file_format)
            else:
                return ""
            base64encoded = base64.b64encode(open(src_file, "rb").read())
            return_value = uri_start + base64encoded.decode()
        make_inline_uri.memo[memo_key] = return_value

    return return_value


make_inline_uri.memo = dict()
