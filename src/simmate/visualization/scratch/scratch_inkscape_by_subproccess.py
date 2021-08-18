# -*- coding: utf-8 -*-

import subprocess


def convert_with_inkscape(file, export_width, export_height):
    try:
        inkscape_path = subprocess.check_output(["which", "inkscape"]).strip()
    except subprocess.CalledProcessError:
        print("ERROR: You need inkscape installed to use this script.")
        exit(1)

    args = [
        inkscape_path,
        "--without-gui",
        "-f",
        file,
        "--export-area-page",
        "-w",
        export_width,
        "-h",
        export_height,
        "--export-png=",
    ]

    print(args)
    subprocess.check_call(args)
