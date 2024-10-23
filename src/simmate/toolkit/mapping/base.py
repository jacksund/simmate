# -*- coding: utf-8 -*-

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer


class ChemSpaceMapper:
    """
    A base class for projecting molecules to 2D chemical space for quick
    visualization.
    """

    @classmethod
    def map_molecules(
        cls,
        molecules: list[Molecule],
        featurizer: Featurizer,
        featurizer_kwargs: dict = {},
        n_outputs: int = 2,  # we want a 2d coords output by default
        **kwargs,
    ) -> tuple:
        fingerprints = featurizer.featurize_many(molecules, **featurizer_kwargs)
        clusters = cls.map_fingerprints(
            fingerprints=fingerprints,
            n_outputs=n_outputs,
            **kwargs,
        )
        # TODO: we may want to adapt how mapping info is returned
        #   e.g... a list of molecules, add to pandas df column, etc.
        return clusters

    @classmethod
    def map_fingerprints(
        cls,
        fingerprints: list,
        n_outputs: int = 2,
        **kwargs,
    ):
        raise NotImplementedError("a map_fingerprints method must be defined")

    # -------------------------------------------------------------------------

    @classmethod
    def from_preset(
        cls,
        preset: str,
        method: str = "map_molecules",
        **kwargs,
    ):
        if preset == "umap-morgan":
            from simmate.toolkit.featurizers import MorganFingerprint
            from simmate.toolkit.mapping import Umap

            mapping_method = getattr(Umap, method)
            mapping_result = mapping_method(
                featurizer=MorganFingerprint,
                **kwargs,
            )
            return mapping_result

        else:
            raise Exception("Unknown preset provided")
