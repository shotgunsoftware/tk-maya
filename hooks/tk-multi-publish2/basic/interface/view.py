"""User interface code for the Maya publishers at the Netherlands Film Academy.
The existing tk-multi-publish2 way of storing widget data is a bit annoying to work with,
so I decided to sort of bootstrap my own little Qt application into tk-multi-publish2.
This way everything still looks the same for our artists, but it is much more flexible and powerful
under the hood.

Written by Mervin van Brakel, 2024
"""

from PySide2 import QtCore, QtWidgets

from . import constants


class PublishUserInterface(QtWidgets.QWidget):
    def __init__(self, publisher_type: constants.PublisherType, parent=None):
        super().__init__()
        self.create_user_interface(publisher_type)

    def create_user_interface(self, publisher_type):
        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        layout.addWidget(self.get_publish_list_widget(), 1)
        layout.addWidget(self.get_publish_settings_widget(publisher_type), 5)

    def get_publish_list_widget(self) -> QtWidgets.QWidget:
        """Returns a widget that contains a list of items that will be published."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)

        self.publish_list = QtWidgets.QListView()
        layout.addWidget(self.publish_list)

        button_layout = QtWidgets.QHBoxLayout()
        add_button = QtWidgets.QPushButton("+")
        button_layout.addWidget(add_button)
        remove_button = QtWidgets.QPushButton("-")
        button_layout.addWidget(remove_button)
        layout.addLayout(button_layout)

        return widget

    def get_publish_settings_widget(self, publisher_type) -> QtWidgets.QWidget:
        """Returns a widget that contains settings for the publish action."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)

        type_label = QtWidgets.QLabel("Type:")
        layout.addWidget(type_label)
        type_dropdown = QtWidgets.QComboBox()
        layout.addWidget(type_dropdown)

        frame_range_label = QtWidgets.QLabel("Frame range:")
        layout.addWidget(frame_range_label)

        frame_range_layout = QtWidgets.QHBoxLayout()
        first_frame = QtWidgets.QSpinBox()
        frame_range_layout.addWidget(first_frame)
        last_frame = QtWidgets.QSpinBox()
        frame_range_layout.addWidget(last_frame)

        if publisher_type == constants.PublisherType.MODEL:
            first_frame.setDisabled(True)
            last_frame.setDisabled(True)

        layout.addLayout(frame_range_layout)

        selection_label = QtWidgets.QLabel("Selection:")
        layout.addWidget(selection_label)

        selection_layout = QtWidgets.QHBoxLayout()
        selection = QtWidgets.QLabel("")
        selection.setStyleSheet("background-color: #000000;")
        selection_layout.addWidget(selection, 5)
        change_selection_button = QtWidgets.QPushButton("Change")
        selection_layout.addWidget(change_selection_button, 1)
        layout.addLayout(selection_layout)

        return widget
