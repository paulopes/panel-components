# -*- coding: utf-8 -*-
from __future__ import print_function, division

import os
import html
import shutil
import base64

try:
    # Detect if running inside a Jupyter notebook
    if "ipykernel" in str(get_ipython()):
        IS_A_JUPYTER_NOTEBOOK = True
    else:
        IS_A_JUPYTER_NOTEBOOK = False
except NameError:
    IS_A_JUPYTER_NOTEBOOK = False


def is_a_number(x):
    try:
        return bool(0 == x * 0)
    except:
        return False


def template_escape(text):
    return text.replace("{{", "{{'{{'}}").replace("{%", "{{'{%'}}")


def get_dir_name(folder=None):
    if not folder:
        folder = os.getcwd()
    return folder.replace("/", os.sep).rstrip(os.sep).split(os.sep)[-1]


def clean_path(path=None):
    if path:
        # Make sure that no root / or upper .. directory names are included.
        return "/".join(
            [
                dir
                for dir in path.strip().rstrip("/").split("/")
                if len(dir) > 0 and dir[0] != "."
            ]
        )
    else:
        return ""


def _read_file(filename, folder):
    src_path = os.path.join(folder, filename)
    if not os.path.isfile(src_path):
        src_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), folder, filename
        )

    file_contents = ""
    if os.path.isfile(src_path):
        with open(src_path) as src_file:
            file_contents = src_file.read()

    return file_contents


def get_inline_js(filename, folder):
    return _read_file(filename, folder).replace("</script", r"\u003c/script")


def get_inline_css(filename, folder):
    return _read_file(filename, folder).replace("</style", r"\00003c/style")


def make_available(filename, src_folder, dst_folder, asset_folders):
    filename = filename.strip()
    if dst_folder.endswith("/"):
        dst_folder = dst_folder[:-1]

    file_path_elements = [
        element
        for element in filename.rstrip("/").split("/")
        if len(element) > 0 and element[0] != "."
    ]
    dst_folder = os.sep.join([dst_folder] + file_path_elements[:-1])
    dst_file = os.path.join(dst_folder, file_path_elements[-1])

    if not os.path.isfile(dst_file):

        if not os.path.exists(dst_folder):
            try:
                os.makedirs(dst_folder)
            except OSError as e:  # Guard against race condition
                if e.errno != errno.EEXIST:
                    raise

        src_file = os.path.join(src_folder, *file_path_elements)
        src_exists = False
        if os.path.isfile(src_file):
            src_exists = True
        elif asset_folders:
            for folder in reversed(asset_folders):
                folder_path_elements = [
                    element
                    for element in folder.rstrip("/").split("/")
                    if len(element) > 0 and element[0] != "."
                ]
                if folder[0] == "/":
                    folder_path_elements[0] = "/" + folder_path_elements[0]
                src_file = os.path.join(*folder_path_elements, *file_path_elements)
                if os.path.isfile(src_file):
                    src_exists = True
                    break

        if src_exists:
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
        if os.path.isfile(src_file):
            src_exists = True
    else:
        file_path_elements = [
            element
            for element in src_file.strip("/").split("/")
            if len(element) > 0 and element[0] != "."
        ]

        src_file = os.path.join(src_folder, *file_path_elements)
        if os.path.isfile(src_file):
            src_exists = True
        elif asset_folders:
            for folder in reversed(asset_folders):
                folder_path_elements = [
                    element
                    for element in folder.strip("/").split("/")
                    if len(element) > 0 and element[0] != "."
                ]
                src_file = os.path.join(*folder_path_elements, *file_path_elements)
                if os.path.isfile(src_file):
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
                uri_start = "data:application/x-font-{};charset=utf8;base64,".format(
                    file_format
                )
            else:
                return ""
            base64encoded = base64.b64encode(open(src_file, "rb").read())
            return_value = uri_start + base64encoded.decode()
        make_inline_uri.memo[memo_key] = return_value

    return return_value


make_inline_uri.memo = dict()
