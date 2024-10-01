"""User interface code for the Maya publishers at the Netherlands Film Academy.
The existing tk-multi-publish2 way of storing widget data is a bit annoying to work with,
so I decided to sort of bootstrap my own little Qt application into tk-multi-publish2.
This way everything still looks the same for our artists, but it is much more flexible and powerful
under the hood.

Written by Mervin van Brakel, 2024
"""

from PySide2 import QtCore, QtWidgets

from . import data_structures, models, maya_interfacing


class PublishUserInterface(QtWidgets.QWidget):
    def __init__(self, publisher_type: data_structures.PublisherType, parent=None):
        super().__init__()
        self.publish_model = models.PublishDataModel(publisher_type)
        self.create_user_interface()
        self.populate_settings_widget()
        self.populating = False  # Shitty fix so the combobox update event doesn't trigger when it's not supposed to

        self.publish_list.selectionModel().selectionChanged.connect(
            self.on_new_publish_selected
        )
        self.type_dropdown.currentIndexChanged.connect(self.change_publisher)

    def create_user_interface(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        layout.addWidget(self.get_publish_list_widget(), 1)
        layout.addWidget(self.get_publish_settings_widget(), 5)

    def get_publish_list_widget(self) -> QtWidgets.QWidget:
        """Returns a widget that contains a list of items that will be published."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)

        self.publish_list = QtWidgets.QListView()
        self.publish_list.setModel(self.publish_model)

        if self.publish_model.rowCount() > 0:
            self.publish_list.setCurrentIndex(self.publish_model.index(0, 0))

        layout.addWidget(self.publish_list)

        button_layout = QtWidgets.QHBoxLayout()
        add_button = QtWidgets.QPushButton("+")
        add_button.clicked.connect(self.add_publish)
        button_layout.addWidget(add_button)

        remove_button = QtWidgets.QPushButton("-")
        remove_button.clicked.connect(self.remove_publish)
        button_layout.addWidget(remove_button)
        layout.addLayout(button_layout)

        return widget

    def get_publish_settings_widget(self) -> QtWidgets.QWidget:
        """Returns a widget that contains settings for the publish action."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)

        type_label = QtWidgets.QLabel("Type:")
        layout.addWidget(type_label)
        self.type_dropdown = QtWidgets.QComboBox()
        layout.addWidget(self.type_dropdown)

        frame_range_label = QtWidgets.QLabel("Frame range:")
        layout.addWidget(frame_range_label)

        frame_range_layout = QtWidgets.QHBoxLayout()
        self.first_frame = QtWidgets.QSpinBox()
        self.first_frame.setRange(0, 99999)
        self.first_frame.valueChanged.connect(self.change_first_frame)
        frame_range_layout.addWidget(self.first_frame)
        self.last_frame = QtWidgets.QSpinBox()
        self.last_frame.setRange(0, 99999)
        self.last_frame.valueChanged.connect(self.change_last_frame)
        frame_range_layout.addWidget(self.last_frame)

        layout.addLayout(frame_range_layout)

        selection_label = QtWidgets.QLabel("Selection:")
        layout.addWidget(selection_label)

        selection_layout = QtWidgets.QHBoxLayout()
        self.selection = QtWidgets.QLabel("")
        self.selection.setWordWrap(False)
        self.selection.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
        )
        self.selection.setStyleSheet("background-color: #000000;")
        selection_layout.addWidget(self.selection, 5)
        change_selection_button = QtWidgets.QPushButton("Update")
        change_selection_button.clicked.connect(self.change_maya_selection)
        selection_layout.addWidget(change_selection_button, 1)
        layout.addLayout(selection_layout)

        return widget

    def populate_settings_widget(self):
        """Populates the settings widget with the data of the selected publish."""
        self.populating = True
        stored_publish_data = self.publish_model.data(
            self.publish_list.currentIndex(), QtCore.Qt.UserRole
        )
        if stored_publish_data is None:
            return

        self.type_dropdown.clear()
        for publisher in self.publish_model.get_available_publishers():
            self.type_dropdown.addItem(publisher.value, publisher)

        self.type_dropdown.setCurrentIndex(
            self.type_dropdown.findText(stored_publish_data.publisher.value)
        )
        self.first_frame.setValue(stored_publish_data.first_frame)
        self.last_frame.setValue(stored_publish_data.last_frame)
        self.selection.setText(str(stored_publish_data.selection).replace("|", " / "))

        if self.publish_model.publisher_type == data_structures.PublisherType.MODEL:
            self.first_frame.setDisabled(True)
            self.last_frame.setDisabled(True)
        self.populating = False

    def add_publish(self):
        """Prompts the user for a publish name and stores the new publish data on the model."""
        name_dialog = PublishNameDialog(self.publish_model.get_publish_names())

        if name_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        selection = (
            maya_interfacing.get_current_selection()[0]
            if len(maya_interfacing.get_current_selection()) == 1
            else ""
        )

        self.publish_model.add_publish(
            name_dialog.get_name(),
            maya_interfacing.get_project_frame_range(),
            selection,
        )

    def remove_publish(self):
        """Removes the selected publish from the model."""
        self.publish_model.remove_publish(self.publish_list.currentIndex())

    def on_new_publish_selected(self, _, __):
        """Called when a new publish is selected in the list."""
        self.populate_settings_widget()

    def change_publisher(self, new_publisher_index) -> None:
        """Changes the stored publisher of the publish and saves the data."""
        new_publisher = self.type_dropdown.itemData(new_publisher_index)
        if new_publisher is None or self.populating:
            return

        stored_publish_data = self.publish_model.data(
            self.publish_list.currentIndex(), QtCore.Qt.UserRole
        )
        stored_publish_data.publisher = new_publisher
        self.publish_model.save_publish_data()

    def change_first_frame(self, new_value: int) -> None:
        """Changes the first frame of the publish and saves the data."""
        stored_publish_data = self.publish_model.data(
            self.publish_list.currentIndex(), QtCore.Qt.UserRole
        )
        stored_publish_data.first_frame = new_value
        self.publish_model.save_publish_data()

    def change_last_frame(self, new_value: int) -> None:
        """Changes the last frame of the publish and saves the data."""
        stored_publish_data = self.publish_model.data(
            self.publish_list.currentIndex(), QtCore.Qt.UserRole
        )
        stored_publish_data.last_frame = new_value
        self.publish_model.save_publish_data()

    def change_maya_selection(self):
        """Prompts the user to select a new root item for the publish."""
        selection = maya_interfacing.get_current_selection()

        if len(selection) != 1:
            if len(selection) > 1:
                error_message = "You can only select 1 root item for exporting. Make multiple publishes for multiple root items or group them together and select the group."
            else:
                error_message = "You need to select a root item for exporting."
            error_dialog = QtWidgets.QMessageBox()
            error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
            error_dialog.setText(error_message)
            error_dialog.setWindowTitle("Selection Error")
            error_dialog.exec_()
            return

        stored_publish_data = self.publish_model.data(
            self.publish_list.currentIndex(), QtCore.Qt.UserRole
        )
        stored_publish_data.selection = selection[0]
        self.publish_model.save_publish_data()
        self.populate_settings_widget()


class PublishNameDialog(QtWidgets.QDialog):
    """Dialog with a text input field for the name of the publish."""

    def __init__(self, existing_names: list, parent=None):
        super().__init__(parent)
        self.existing_names = existing_names
        self.create_user_interface()

    def create_user_interface(self):
        """Creates the user interface for the dialog."""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        label = QtWidgets.QLabel("Publish name: (a-z only):")
        layout.addWidget(label)

        self.name_input = QtWidgets.QLineEdit("main")
        self.name_input.textChanged.connect(self.validate_input)
        layout.addWidget(self.name_input)

        button_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.validate_input()

    def validate_input(self):
        """Validates the input to ensure it contains only lowercase letters."""
        text = self.name_input.text()
        if text.islower() and text.isalpha() and text not in self.existing_names:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def get_name(self):
        """Returns the name that was entered in the dialog."""
        return self.name_input.text()
