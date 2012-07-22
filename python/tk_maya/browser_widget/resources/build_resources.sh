#!/usr/bin/env bash
# 
# Copyright (c) 2008 Shotgun Software, Inc
# ----------------------------------------------------

echo "Building UIs for PyQt4..."

pyuic4 --from-imports header.ui  > ../ui_pyqt4/header.py
pyuic4 --from-imports item.ui    > ../ui_pyqt4/item.py
pyuic4 --from-imports browser.ui > ../ui_pyqt4/browser.py
pyrcc4 resources.qrc             > ../ui_pyqt4/resources_rc.py

echo "Building UIs for PySide..."

pyside-uic --from-imports header.ui  > ../ui_pyside/header.py
pyside-uic --from-imports item.ui    > ../ui_pyside/item.py
pyside-uic --from-imports browser.ui > ../ui_pyside/browser.py
pyside-rcc resources.qrc             > ../ui_pyside/resources_rc.py

echo "All done!"