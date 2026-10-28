from simmate.toolkit import Molecule

from .base import Featurizer


class PropertyGrabber(Featurizer):
    """
    Grabs attributes from the molecule object
    """

    @classmethod
    def get_feature_names(cls, properties: list[str], **kwargs) -> list[str]:
        # the list of property names is given by the user and we just copy it
        # over so that higher level features can use it
        return properties

    @staticmethod
    def featurize(
        molecule: Molecule,
        properties: list[str],  # e.g. ["num_rings", "molecular_weight", ...]
        **kwargs,
    ) -> list:
        # a plain list, so values of mixed types (e.g. a str next to floats) keep
        # their own types
        return [getattr(molecule, p) for p in properties]
