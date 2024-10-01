"""Code that interfaces with Maya for storing and retrieving our publish settings.

Written by Mervin van Brakel, 2024
"""

import json
from typing import List, Union

from maya import cmds

from . import data_structures


def get_publish_settings(
    publisher_type: data_structures.PublisherType,
) -> List[data_structures.PublishData]:
    """Retrieves the stored publish data from the Maya file for the given publisher type.

    Args:
        publisher_type: The type of publisher to retrieve the settings for.

    Returns:
        A list of publish data objects that contain the stored settings.
    """
    stored_publish_data = cmds.fileInfo(publisher_type.storage_name, q=True)

    if len(stored_publish_data) == 0:
        return []

    parsed_publish_data = json.loads(
        stored_publish_data[0].encode("utf-8").decode("unicode_escape")
    )

    retrieved_publish_data = []
    for publish_data in parsed_publish_data:
        name = publish_data
        publisher = get_publisher_from_publisher_type_and_name(
            publisher_type, parsed_publish_data[publish_data]["publisher"]
        )
        first_frame = parsed_publish_data[publish_data]["first_frame"]
        last_frame = parsed_publish_data[publish_data]["last_frame"]
        selection = parsed_publish_data[publish_data]["selection"]

        retrieved_publish_data.append(
            data_structures.PublishData(
                name, publisher_type, publisher, first_frame, last_frame, selection
            )
        )

    return retrieved_publish_data


def get_publisher_from_publisher_type_and_name(
    publisher_type: data_structures.PublisherType, publisher_name: str
) -> Union[
    data_structures.AnimationPublisher,
    data_structures.CameraPublisher,
    data_structures.ModelPublisher,
]:
    """Returns the right publisher for the given publisher type and name.

    Args:
        publisher_type: The type of publisher.
        name: The name of the publisher.

    Returns:
        The publisher for the given publisher type and name.
    """
    if publisher_type == data_structures.PublisherType.ANIMATION:
        return data_structures.AnimationPublisher(publisher_name)

    if publisher_type == data_structures.PublisherType.CAMERA:
        return data_structures.CameraPublisher(publisher_name)

    if publisher_type == data_structures.PublisherType.MODEL:
        return data_structures.ModelPublisher(publisher_name)

    return None


def store_publish_settings(
    publisher_type: data_structures.PublisherType,
    publish_data: List[data_structures.PublishData],
):
    """Stores the publish settings in the Maya file.

    Args:
        publisher_type: The type of publisher to store the settings for.
        publish_data: The publish data to store.
    """
    publish_data_to_store = {}
    for data in publish_data:
        publish_data_to_store[data.name] = {
            "publisher": data.publisher.value,
            "first_frame": data.first_frame,
            "last_frame": data.last_frame,
            "selection": data.selection,
        }

    cmds.fileInfo(publisher_type.storage_name, json.dumps(publish_data_to_store))


def get_project_frame_range() -> List[int]:
    """Returns the frame range of the project.

    Returns:
        A list with the first and last frame of the project.
    """
    return [
        int(cmds.playbackOptions(q=True, minTime=True)),
        int(cmds.playbackOptions(q=True, maxTime=True)),
    ]


def get_current_selection() -> List[str]:
    """Returns the current selection in the scene.

    Returns:
        A list with the currently selected objects.
    """
    return cmds.ls(selection=True, long=True)
