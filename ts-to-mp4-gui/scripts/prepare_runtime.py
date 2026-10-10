"""Collect the build runtime's notices without launching a GUI window."""
import shutil
import struct
import sys
import tkinter
from pathlib import Path


def main():
    if sys.platform != 'win32' or struct.calcsize('P') != 8:
        raise RuntimeError('Build requires 64-bit Windows Python.')
    tcl_root = Path(tkinter.Tcl().eval('info library'))
    notices = Path(sys.argv[1]) / 'licenses'
    notices.mkdir(parents=True, exist_ok=True)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    shutil.copy2(python_license, notices / 'Python-LICENSE.txt')
    # Official Windows Python includes Tcl/Tk terms in its aggregate LICENSE.
    # Some installations also ship standalone license.terms files.
    combined = python_license.read_text(encoding='utf-8')
    tcl_license = tcl_root / 'license.terms'
    if tcl_license.is_file():
        shutil.copy2(tcl_license, notices / 'Tcl-license.terms')
    elif 'Scriptics Corporation' not in combined:
        raise RuntimeError('Tcl license not found in runtime or Python LICENSE.txt.')
    tk_licenses = sorted(tcl_root.parent.glob('tk*/license.terms'))
    if tk_licenses:
        shutil.copy2(tk_licenses[0], notices / 'Tk-license.terms')
    elif 'Apple Inc.' not in combined or 'Scriptics Corporation' not in combined:
        raise RuntimeError('Tk license not found in runtime or Python LICENSE.txt.')


if __name__ == '__main__':
    main()
