import sys
import html
import base64
import pyperclip


if len(sys.argv) <= 1:
    print(
        """
        Convert a provided font file into an url( parameter
        data URI string suitable to be used in a .CSS file."""
    )
    exit()

filename = sys.argv[1]
if filename.lower().endswith(".svg"):
    svg = open(filename).read()
    start = svg.find("<svg")
    start = svg.find("<SVG") if start < 0 else start
    pyperclip.copy(
        'url("data:image/svg+xml;charset=utf8,'
        + html.escape(svg[start:])
        + '") format("svg");'
    )
    print("The .SVG font's URI text has been copied to the clipboard")
else:
    format = filename.split(".")[-1]
    base64encoded = base64.b64encode(open(filename, "rb").read())
    pyperclip.copy(
        "url(data:application/x-font-woff;charset=utf8;base64,"
        + base64encoded.decode()
        + ') format("'
        + format.lower()
        + '");'
    )
    print("The ." + format.upper() + "font's URI text has been copied to the clipboard")
