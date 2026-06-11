from enum import Enum


class Breed(Enum):
    """Enum indicating the breed of the animal."""

    HO = "Holstein"
    JE = "Jersey"
    # Beef breeds (NRC 2016 Table 19-1)
    AN = "Angus"
    HE = "Hereford"
    SI = "Simmental"
    CH = "Charolais"
    LM = "Limousin"
    BR = "Brahman"
    XB = "Crossbred"


class Sex(Enum):
    """Enum indicating the sex of the animal."""

    MALE = "male"
    FEMALE = "female"
    STEER = "steer"


class AnimalStatus(Enum):
    """Enum indicating the status of the animal after performing daily routines update."""

    REMAIN = "remain"
    LIFE_STAGE_CHANGED = "life stage changed"
    DEAD = "dead"
    SOLD = "sold"
    STILLBORN = "stillborn"
