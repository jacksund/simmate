# -*- coding: utf-8 -*-

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer
from simmate.toolkit.similarity.base import SimilarityEngine


class ClusteringEngine:
    """
    A base class for clustering molecules using various fingerprinting
    and similarity methods.
    """

    @classmethod
    def cluster_molecules(
        cls,
        molecules: list[Molecule],
        featurizer: Featurizer,
        similarity_engine: SimilarityEngine,
        featurizer_kwargs: dict = {},
        similarity_engine_kwargs: dict = {},
        **kwargs,
    ):
        fingerprints = featurizer.featurize_many(molecules, **featurizer_kwargs)
        clusters = cls.cluster_fingerprints(
            fingerprints,
            similarity_engine,
            similarity_engine_kwargs,
            **kwargs,
        )
        # TODO: we may want to adapt how cluster info is returned
        #   e.g... a list of molecules, add to pandas df column, etc.
        return clusters

    @classmethod
    def cluster_fingerprints(
        cls,
        fingerprints: list,
        similarity_engine: SimilarityEngine,
        similarity_engine_kwargs: dict = {},
        **kwargs,
    ):
        # This is a default method that can be overwritten
        similarity_matrix = similarity_engine.get_similarity_matrix(
            fingerprints,
            **similarity_engine_kwargs,
        )
        return cls.cluster_similarity_matrix(similarity_matrix, **kwargs)

    @classmethod
    def cluster_similarity_matrix(cls, similarity_matrix: list[list]):
        raise NotImplementedError(
            "This class does not provide a `cluster_similarity_matrix` method."
        )

    # -------------------------------------------------------------------------

    @classmethod
    def from_preset(
        cls,
        preset: str,
        method: str = "cluster_molecules",
        **kwargs,
    ):
        if preset == "butina-tanimoto-morgan":
            from simmate.toolkit.clustering import Butina
            from simmate.toolkit.featurizers import MorganFingerprint
            from simmate.toolkit.similarity import Tanimoto

            cluster_method = getattr(Butina, method)
            clusters = cluster_method(
                featurizer=MorganFingerprint,
                similarity_engine=Tanimoto,
                **kwargs,
            )
            return clusters

        elif preset == "murko_scaffold":
            from simmate.toolkit.clustering import Identity as ClusterIdentity
            from simmate.toolkit.featurizers import PropertyGrabber
            from simmate.toolkit.similarity import Identity

            if method != "cluster_molecules":
                raise Exception(
                    "Only the 'cluster_molecules' method is supported for this preset"
                )

            cluster_method = getattr(ClusterIdentity, "cluster_molecules")
            clusters = cluster_method(
                featurizer=PropertyGrabber,
                similarity_engine=Identity,
                featurizer_kwargs={"properties": ["murko_scaffold"]},
                **kwargs,
            )
            return clusters

        else:
            raise Exception(f"Unknown preset provided: {preset}")
