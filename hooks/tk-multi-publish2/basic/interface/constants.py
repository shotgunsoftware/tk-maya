"""Constants for the tk-multi-publish2 Maya publishers at the Netherlands Film Academy.

Written by Mervin van Brakel, 2024."""

from enum import Enum


class PublisherType(Enum):
    """Class that stores types of publishers available."""

    ANIMATION = "Animation"
    CAMERA = "Camera"
    MODEL = "Model"
