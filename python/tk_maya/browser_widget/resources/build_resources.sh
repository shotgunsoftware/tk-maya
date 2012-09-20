#!/usr/bin/env bash
# 
# Copyright (c) 2008 Shotgun Software, Inc
# ----------------------------------------------------


echo "Building UIs for PySide..."

pyside-uic --from-imports header.ui  > ../ui_pyside/header.py
pyside-uic --from-imports item.ui    > ../ui_pyside/item.py
pyside-uic --from-imports browser.ui > ../ui_pyside/browser.py
pyside-rcc resources.qrc             > ../ui_pyside/resources_rc.py

echo "All done!"