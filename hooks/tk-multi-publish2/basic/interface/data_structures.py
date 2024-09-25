"""Constants for the tk-multi-publish2 Maya publishers at the Netherlands Film Academy.

Written by Mervin van Brakel, 2024."""

from dataclasses import dataclass
from enum import Enum
from typing import Union


class AnimationPublisher(Enum):
    """Class that stores types of animation publishers available."""

    USD = "USD"
    ALEMBIC = "Alembic"


class CameraPublisher(Enum):
    """Class that stores types of camera publishers available."""

    USD = "USD"
    ALEMBIC = "Alembic"


class ModelPublisher(Enum):
    """Class that stores types of model publishers available."""

    ALEMBIC = "Alembic"
    FBX = "FBX"


class PublisherType(Enum):
    """Class that stores types of publishers available."""

    ANIMATION = ("NFA_animation_publish", AnimationPublisher, AnimationPublisher.USD)
    CAMERA = ("NFA_camera_publish", CameraPublisher, CameraPublisher.USD)
    MODEL = ("NFA_model_publish", ModelPublisher, ModelPublisher.ALEMBIC)

    def __init__(
        self,
        storage_name: str,
        available_publishers_enum: Union[
            AnimationPublisher, CameraPublisher, ModelPublisher
        ],
        default_publisher: Union[AnimationPublisher, CameraPublisher, ModelPublisher],
    ):
        self.storage_name = storage_name
        self.available_publishers_enum = available_publishers_enum
        self.default_publisher = default_publisher


@dataclass
class PublishData:
    """Data class that stores data for the publishers."""

    name: str
    publish_type: PublisherType
    publisher: Union[AnimationPublisher, CameraPublisher, ModelPublisher]
    first_frame: int
    last_frame: int
    selection: str
