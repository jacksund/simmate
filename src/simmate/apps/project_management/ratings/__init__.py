from .base import RatingSystem
from .elo import Elo
from .glicko import Glicko

RATING_SYSTEMS: dict[str, type[RatingSystem]] = {
    "glicko": Glicko,
    "elo": Elo,
}
"""
All rating systems that a project can use, keyed by the value stored in
`Project.rating_system`.
"""
