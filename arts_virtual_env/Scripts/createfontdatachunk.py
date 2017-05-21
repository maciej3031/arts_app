#!d:\maciej\dropbox\dropbox\praca\programowanie\01_python\02_python_files\02_projects\02_big_projects\10_articles_site\10_articles\arts_virtual_env\scripts\python.exe
from __future__ import print_function
import base64
import os
import sys

if __name__ == "__main__":
    # create font data chunk for embedding
    font = "Tests/images/courB08"
    print("    f._load_pilfont_data(")
    print("         # %s" % os.path.basename(font))
    print("         BytesIO(base64.decodestring(b'''")
    base64.encode(open(font + ".pil", "rb"), sys.stdout)
    print("''')), Image.open(BytesIO(base64.decodestring(b'''")
    base64.encode(open(font + ".pbm", "rb"), sys.stdout)
    print("'''))))")
