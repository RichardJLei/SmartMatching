from enum import Enum

class LocationType(str, Enum):
    """Enum for file location types"""
    LOCAL = "local"
    CLOUD = "cloud" 