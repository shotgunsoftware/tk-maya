"""Qt models for the Maya publishing system at the Netherlands Film Academy

Written by Mervin van Brakel, 2024.
"""

from typing import List

from PySide2 import QtCore

from . import data_structures, maya_interfacing


class PublishDataModel(QtCore.QAbstractListModel):
    """Model that stores all publish data for a specific publish type."""

    def __init__(self, publish_type, parent=None) -> None:
        """Initializes the model with the stored publish data."""
        super().__init__(parent)
        self.stored_publish_data: List[data_structures.PublishData] = (
            maya_interfacing.get_publish_settings(publish_type)
        )

    def rowCount(self, parent) -> int:
        """Called by Qt to get the amount of rows to display."""
        return len(self.data)

    def data(self, index: QtCore.QModelIndex, role) -> str:
        """Called by Qt to get the data to display in the given row.

        Args:
            index: The index of the row to get the data for.
            role: The role to get the data for.
        """
        if role == QtCore.Qt.DisplayRole:
            return self.stored_publish_data[index.row()].name

        return None

    def flags(self, index) -> QtCore.Qt.ItemFlags:
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
