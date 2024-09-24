"""Constants for the tk-multi-publish2 Maya publishers at the Netherlands Film Academy.

Written by Mervin van Brakel, 2024."""

from dataclasses import dataclass
from enum import Enum
from typing import Union


class PublisherType(Enum):
    """Class that stores types of publishers available."""

    ANIMATION = "NFA_animation_publish"
    CAMERA = "NFA_camera_publish"
    MODEL = "NFA_model_publish"


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

    FBX = "FBX"
    ALEMBIC = "Alembic"


@dataclass
class PublishData:
    """Data class that stores data for the publishers."""

    name: str
    publish_type: PublisherType
    publisher: Union[AnimationPublisher, CameraPublisher, ModelPublisher]
    first_frame: int
    last_frame: int
    selection: str
