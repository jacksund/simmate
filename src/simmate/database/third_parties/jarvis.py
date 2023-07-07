# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Structure, table_column


class JarvisStructure(Structure):
    """
    Crystal structures from the [JARVIS](https://jarvis.nist.gov/) database.

    Currently, this table only stores strucure and reported energy above hull.
    The calculated energy is not reported, so the Thermodynamics mixin is not used.
    """

    class Meta:
        app_label = "data_explorer"

    archive_fields = ["energy_above_hull"]
    api_filters = dict(
        energy_above_hull=["range"],
    )
    source = "JARVIS"
    source_long = "Joint Automated Repository for Various Integrated Simulations"
    homepage = "https://jarvis.nist.gov/"
    source_doi = "https://doi.org/10.1038/s41524-020-00440-1"
    remote_archive_link = "https://archives.simmate.org/JarvisStructure-2023-07-07.zip"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "jvasp-12345")
    """

    # TODO: contact their team to ask about reporting energy instead. That way
    # we can use the Thermodynamics mixin instead of manually listing this.
    energy_above_hull = table_column.FloatField(blank=True, null=True)
    """
    The energy above hull, as reported by the JARVIS database (no units given)
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the JARVIS website.
        """
        # All JARVIS structures have their data mapped to a URL in the same way
        # ex: https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/JVASP-1234.xml
        # we store the id as "jvasp-123" so we need to convert this to uppercase
        id = self.id.upper()
        return f"https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/{id}.xml"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_all_structures(cls):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        This method pulls JARVIS data into the Simmate database.

        JARVIS has a python package "jarvis-tools" that let's us pull some of
        their database dumps. For instructions on how to do this, they provided
        [this link](https://colab.research.google.com/github/knc6/jarvis-tools-notebooks/blob/master/jarvis-tools-notebooks/Get_JARVIS_DFT_final_structures_in_ASE_or_Pymatgen_format.ipynb)

        Alternatively, we could manually download
        [their database json files](https://jarvis-materials-design.github.io/dbdocs/thedownloads/). We specifically look at the "3D-materials curated data".
        """

        from rich.progress import track

        from simmate.toolkit import Structure as ToolkitStructure

        # Jarvis is not a dependency of simmate, so make sure you install it
        # before using this method
        try:
            from jarvis.db.figshare import data as jarvis_helper
        except:
            raise ModuleNotFoundError(
                "You must install jarvis with `conda install -c conda-forge jarvis-tools`"
            )

        # Load all of the 3D data from JARVIS. This gives a list of dictionaries
        # TODO: In the future, we can add other datasets like the 2D dataset.
        data = jarvis_helper("dft_3d")

        # Now iterate through all the data -- which is a list of dictionaries.
        # We convert the data into a pymatgen object and sanitize it before
        # saving to the Simmate database
        db_objects = []
        for entry in track(data):
            # The structure is in the atoms field as a dictionary. We pull
            # this data out and convert it to a pymatgen Structure object
            structure = ToolkitStructure(
                lattice=entry["atoms"]["lattice_mat"],
                species=entry["atoms"]["elements"],
                coords=entry["atoms"]["coords"],
                coords_are_cartesian=entry["atoms"]["cartesian"],
            )

            # now convert the entry to a database object
            structure_db = cls.from_toolkit(
                id=entry["jid"].lower(),
                structure=structure,
                energy_above_hull=entry["ehull"] if entry["ehull"] != "na" else None,
            )

            db_objects.append(structure_db)

        # and save it to our database
        cls.objects.bulk_create(
            db_objects,
            batch_size=15000,
            ignore_conflicts=True,
        )
