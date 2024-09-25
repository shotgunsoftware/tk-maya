"""Qt models for the Maya publishing system at the Netherlands Film Academy

Written by Mervin van Brakel, 2024.
"""

from typing import List, Union

from PySide2 import QtCore

from . import data_structures, maya_interfacing


class PublishDataModel(QtCore.QAbstractListModel):
    """Model that stores all publish data for a specific publish type."""

    def __init__(
        self, publish_type: data_structures.PublisherType, parent=None
    ) -> None:
        """Initializes the model with the stored publish data."""
        super().__init__(parent)
        self.stored_publish_data: List[data_structures.PublishData] = (
            maya_interfacing.get_publish_settings(publish_type)
        )
        self.publisher_type = publish_type

    def rowCount(self, parent=None) -> int:
        """Called by Qt to get the amount of rows to display."""
        return len(self.stored_publish_data)

    def data(
        self, index: QtCore.QModelIndex, role
    ) -> Union[str, data_structures.PublishData]:
        """Returns stored publish data based on data type.

        Args:
            index: The index of the row to get the data for.
            role: The role to get the data for.
        """
        if role == QtCore.Qt.DisplayRole:
            return self.stored_publish_data[index.row()].name

        if role == QtCore.Qt.UserRole:
            try:
                return self.stored_publish_data[index.row()]
            except IndexError:
                return None

        return None

    def flags(self, index) -> QtCore.Qt.ItemFlags:
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def get_available_publishers(self) -> list:
        """Returns the available publishers for the publisher type."""
        return list(self.publisher_type.available_publishers_enum)

    def add_publish(
        self, publish_name: str, frame_range: List[int], selection: str
    ) -> None:
        """Adds a new publish to the list and stores it in the Maya file."""
        self.stored_publish_data.append(
            data_structures.PublishData(
                publish_name,
                self.publisher_type,
                self.publisher_type.default_publisher,
                frame_range[0],
                frame_range[1],
                selection,
            )
        )

        maya_interfacing.store_publish_settings(
            self.publisher_type, self.stored_publish_data
        )
        self.layoutChanged.emit()

    def remove_publish(self, index: QtCore.QModelIndex) -> None:
        """Removes a publish from the list and stores the new list in the Maya file."""
        self.stored_publish_data.pop(index.row())
        maya_interfacing.store_publish_settings(
            self.publisher_type, self.stored_publish_data
        )
        self.layoutChanged.emit()

    def save_publish_data(self) -> None:
        """Saves the publish data in the Maya file."""
        maya_interfacing.store_publish_settings(
            self.publisher_type, self.stored_publish_data
        )
