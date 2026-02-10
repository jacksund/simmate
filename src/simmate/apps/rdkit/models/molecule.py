# -*- coding: utf-8 -*-

import pandas
from django.contrib.postgres import indexes
from django.db.models import Func

from simmate.apps.rdkit.models import custom_fields
from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable, SearchResults, table_column
from simmate.toolkit import Molecule as ToolkitMolecule


class MoleculeSearchResults(SearchResults):

    def filter_molecule_exact(self, molecule: ToolkitMolecule):
        if not isinstance(molecule, ToolkitMolecule):
            molecule = ToolkitMolecule.from_dynamic(molecule)
        return self.filter(inchi_key=molecule.to_inchi_key())

    def filter_molecule_list_exact(self, molecules: list[ToolkitMolecule] | str):
        # TODO: try from_dynamic if it's not a ToolkitMolecule
        if isinstance(molecules, str):
            # assume and try SMILES
            molecules = [ToolkitMolecule.from_smiles(m) for m in molecules.split(".")]
        inchi_keys = [m.to_inchi_key() for m in molecules]
        return self.filter(inchi_key__in=inchi_keys)

    def filter_substructure(self, molecule_query: ToolkitMolecule):

        if not isinstance(molecule_query, ToolkitMolecule):
            molecule_query = ToolkitMolecule.from_dynamic(molecule_query)

        # TODO: accept SMARTS toolkit object
        # This code effectively adds something like...
        #   SELECT ...., rdkit_mol@>'CCC' as "substructure_match" WHERE ... AND rdkit_mol@>'CCC'
        # Where "CCC" is an example substructure SMARTS query
        return self.annotate(
            substructure_match=Func(
                "rdkit_mol",  # the rdkit_mol of the same row/obj
                smiles=molecule_query.to_smiles(),
                function="@>",
                # "::qmol" allows us to use SMARTS in addition to SMILES
                template="%(expressions)s%(function)s'%(smiles)s'::qmol",
                output_field=table_column.BooleanField(),
            )
        ).filter(
            substructure_match=True,
        )

    def filter_similarity_2d(
        self,
        molecule: ToolkitMolecule,
        cutoff: float = 0.5,  # None and 0 disable filtering
        order: bool = True,
    ) -> pandas.DataFrame:
        if not isinstance(molecule, ToolkitMolecule):
            molecule = ToolkitMolecule.from_dynamic(molecule)
        queryset = self.annotate(
            similarity_2d=Func(
                "fingerprint_morganbv",  # the column that holds the fingerprint
                reference_molecule=molecule.to_smiles(),
                function="tanimoto_sml",
                template="%(function)s(morganbv_fp(mol_from_smiles('%(reference_molecule)s')),%(expressions)s)",
                output_field=table_column.FloatField(),
            )
        )
        # This code below does the same thing & is easier to read -- but it doesn't
        # allow for use of filter() afterwards, so we opt for the annotate()
        # method above.
        #
        # BUG: injection risk here.
        #   https://docs.djangoproject.com/en/4.2/topics/db/sql/#passing-parameters-into-raw
        #
        # NOTE: the percent signs are doubled in this query, when the real
        # SQL query they are single! This is because django tries to read
        # them as a formatted string
        #
        # query = (
        #     f"SELECT    *, tanimoto_sml(morganbv_fp(mol_from_smiles('{smiles}')),fingerprint_morganbv) as similarity "
        #     f"FROM      {cls._meta.db_table} "
        #     f"WHERE     morganbv_fp('{smiles}')%%fingerprint_morganbv "
        #     f"ORDER BY  morganbv_fp('{smiles}')<%%>fingerprint_morganbv "
        #     f"LIMIT     {limit};"
        # )
        # results = cls.objects.raw(query)

        if cutoff:
            queryset = queryset.filter(
                similarity_2d__gte=cutoff,
            )
            # OPTIMIZE: Is this running the similarity multiple times? i.e., would
            # a lookup be faster? And I'm not using the '%' operator that rdkit
            # has which might be faster

        if order:
            # reverse order because bigger number = more similar
            queryset = queryset.order_by("-similarity_2d")

        return queryset


class Molecule(DatabaseTable):

    class Meta:
        abstract = True
        indexes = (
            [
                # for faster mol-query searches
                indexes.GistIndex(fields=["rdkit_mol"]),
                # for faster similarity searches
                indexes.GistIndex(fields=["fingerprint_morganbv"]),
            ]
            if settings.postgres_rdkit_extension
            else []
        )

    exclude_from_summary = ["molecule"]
    archive_fields = ["molecule", "molecule_original"]

    # -------------------------------- MANAGER --------------------------------

    objects = MoleculeSearchResults.as_manager()
    # Gives custom filtering methods (ex: filter_substructure)

    # ------------------------------ Base data ------------------------------

    molecule = table_column.TextField(blank=True, null=True)
    """
    The molecule's SDF representation. 
    
    This is a 3D format, but molecules are still limited to 2D coordinates 
    by default. See `is_3d` column.
    
    SDF stands for "structure-data format", which is a chemical table format
    just like 'molfile' and 'ctab' formats. All of these lists each atom in a 
    molecule, the x-y-z coordinates of that atom, and the bonds among the atoms.
    Read more [here](https://en.wikipedia.org/wiki/Chemical_table_file)
    """

    molecule_original = table_column.TextField(blank=True, null=True)
    """
    The original format that this molecule was loaded with. This could be
    SMILES, INCHI, SDF, Molfile, CIF, or some other input accepted by Simmate's 
    toolkit.
    
    Some tables leave this column empty to save on diskspace (e.g. Enamine)
    """

    is_3d = table_column.BooleanField(blank=True, null=True)
    """
    Whether the `molecule` column contains an SDF that is a 2D flattened 
    structure (`is_3d=False`) or 3D conformer (`is_3d=True`).
    """

    # ---------------------- Different molecule formats ----------------------

    smiles = table_column.TextField(blank=True, null=True)
    """
    The molecule's cannonical SMILES representation.
    
    SMILES is short for "Simplified molecular-input line-entry system" and is
    a way to represent molecules in a single line. This representation only 
    captures atom connectivity, while 2D/3D coordinates must be inferred. Also
    multiple molecules/species are separated by a period (".").
    Read more [here](https://en.wikipedia.org/wiki/Simplified_molecular-input_line-entry_system)
    """

    inchi = table_column.TextField(blank=True, null=True)
    """
    The molecule's InChI representation. **Do not confuse with `inchi_key`!**
    
    InChI is short for "International Chemical Identifier" and is designed to 
    provide a standard way to encode molecular information and to facilitate 
    the search for such information in databases and on the web.
    
    This can be viewed as an alternative, more advanced version of SMILES.
    Read more [here](https://en.wikipedia.org/wiki/International_Chemical_Identifier)
    """

    inchi_key = table_column.CharField(
        max_length=30,
        blank=True,
        null=True,
        db_index=True,
    )
    """
    The molecule's InChI Key representation. Sometimes referred to as a hashed
    InChI.
    
    Use this column if you need rapid exact-structure matching. There is also
    a `filter_exact_match` method in our Python API that makes use of this column.
    
    InChI Keys are a fixed length (27 character) digital representation of the 
    InChI that is not human-understandable. They are designed such that the
    same molecule (same InChI) will always give the same InChI Key. But because
    these keys are much shorter than other chemical formats (InChI, SMILES, SDF, 
    ...), the keys allow for very rapid structure searching in database -- 
    specifically, exact-structure matching.
    """

    # ------------------------------ Features ------------------------------

    num_atoms = table_column.IntegerField(blank=True, null=True)
    """
    The total number of atoms in the molecule
    """

    num_stereocenters = table_column.IntegerField(blank=True, null=True)
    """
    The total number of stereocenters in the molecule. This will count
    stereocenters even if stereochemistry is not specified. Does not count
    steric effects.
    """

    num_rings = table_column.IntegerField(blank=True, null=True)
    """
    The total number of atomic rings in the molecule
    """

    num_h_acceptors = table_column.IntegerField(blank=True, null=True)
    """
    Number of hydrogen bond acceptors in the molecule
    """

    num_h_donors = table_column.IntegerField(blank=True, null=True)
    """
    Number of hydrogen bond donors in the molecule
    """

    molecular_weight = table_column.FloatField(blank=True, null=True)
    """
    The average molecular weight of this molecule based on the typical 
    distribution of isotopes for each atom type. Explicitly listed 
    isotopes add/subtract from the average.
    """

    molecular_weight_exact = table_column.FloatField(blank=True, null=True)
    """
    The exact molecular weight of this molecule. Only explicitly specified 
    isotopes are used to calculate this, and if an atom is not explicitly 
    labeled, the most frequently seen "common" isotope is used.
    """

    functional_groups = table_column.JSONField(blank=True, null=True)
    """
    A list of functional groups their corresponding counts for this molecule. If
    the functional group is not listed, then its count is 0.
    
    The full set of ~300 functional groups that we check for are listed 
    [here](#)
    which is pulled from CDK's `SubstructureFingerprinter` class located
    [here](https://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/fingerprint/SubstructureFingerprinter.html)
    
    The data is stored as JSON, which can be sub-queried using both Postgres
    and Python APIs.
    """

    # -------------------------- Predicted properties --------------------------

    log_p_rdkit = table_column.FloatField(blank=True, null=True)
    """
    The *predicted* partition coefficient (Log P) for this molecule using
    RDkit. The method is adapted from Wildman and Crippen JCICS 39:868-73 (1999).
    This is a *rough estimate* of Log P. Higher quality predictions can be made
    using Simmate's workflows (+ third-party QM software).
    
    Log P represents the expected ratio of concentrations that this molecule
    (the solute) would equilabrate between two solvents (e.g. in sep funnel). 
    Here, the standard solvents are octanol and water. Thus, this serves as a 
    measure of the molecule's hydrophobicity. Lower values correspond
    to more hydrophilic molecules. Read more 
    [here](https://en.wikipedia.org/wiki/Partition_coefficient).

    **Do not confuse Log P with Log D**. Log D is pH-dependent and often involves
    a buffer in the solvent. Also log D = log P for non-ionizable compounds at 
    any pH
    """

    tpsa_rdkit = table_column.FloatField(blank=True, null=True)
    """
    The *predicted* topological polar surface area (TPSA) for this molecule using
    RDkit. The method is adapted from [Ertl et al.](https://pubs.acs.org/doi/abs/10.1021/jm000942e).
    RDkit's implementation differs slightly as described 
    [here](https://www.rdkit.org/docs/RDKit_Book.html#implementation-of-the-tpsa-descriptor).
    This is a *rough estimate* of TPSA. Higher quality predictions can be made
    using Simmate's workflows (+ third-party QM software).
           
    The polar surface area (PSA) is the surface area sum over all polar
    atoms (primarily oxygen and nitrogen) and including their 
    attached hydrogen atoms. This is helpful in medicinal chemistry where
    molecules with a polar surface area of greater than 140 angstroms squared
    tend to be poor at permeating cell membranes. Read more 
    [here](https://en.wikipedia.org/wiki/Polar_surface_area)
    """

    synthetic_accessibility = table_column.FloatField(blank=True, null=True)
    """
    The *predicted* synthetic accessibility score (SAS), which is generated 
    using the method from [Ertl et al.](http://www.jcheminf.com/content/1/1/8). 
    Keep in mind that this is a *rough estimate* and that other more robust 
    calculations can be performed to analyze retrosynthetic pathways and 
    molecular stabilities.

    The score is on a 1-10 scale, where lower values correspond to molecules
    that are easier to synthesize. In general, scores are lower for compounds
    that are smaller, are less reactive, have low stereocomplexity, and avoid 
    large + non-standard ring fusions.
    """

    # ------------------------ RDkit-extension fields ------------------------

    # RDkit-extension fields that allow us to do things like substructure
    # and similarity searches directly within postgres

    if settings.postgres_rdkit_extension:

        rdkit_mol = custom_fields.MolField(blank=True, null=True)
        """
        This is the column used for substructure (+ SMARTS) searches. However, we 
        recommend using the `filter_similarity_2d` method in our Python API rather 
        than interact with this column via SQL.
        
        On the surface, this column is a copy of the `smiles` column. But this
        is a special RDkit datatype that allows extra cheminformatics features.
        To perform extra molecule analysis within the database, you can use [the
        additional functions RDkit provides](https://www.rdkit.org/docs/Cartridge.html#functions).                                   
        Keep in mind that many of these functions are available (and more performant)
        in the python toolkit as well.
        """
        # OPTIMIZE: "rdkit_mol" is really just duplicate of the "smiles" column

        fingerprint_morganbv = custom_fields.BfpField(blank=True, null=True)
        """
        This is the column used for 2D similarity searches. However, we recommend
        using the `filter_substructure` method in our Python API rather than
        interact with this column via SQL.
        
        The fingerprint used is a bit vector Morgan fingerprint, which is an
        ECFP-like fingerprint. We use the default radius of 2 Angstroms.
        """

    # ------------------------ TODO fields ------------------------

    # see issue #134 on gitlab for more columns to consider

    # extra columns used by John k:
    # parent_inchikey
    # framework_inchikey
    # unwanted_ss
    # sp3_character
    # num_rotbonds
    # admet_solubility_ppm
    # admet_solubility_moll
    # polarsurfacearea_2d
    # max_level
    # alogp

    @classmethod
    def _from_toolkit(
        cls,
        molecule: ToolkitMolecule | str = None,
        as_dict: bool = False,
        **kwargs,
    ):
        # if there isn't a structure, nothing is to be done.
        if not molecule:
            return kwargs if as_dict else cls(**kwargs)

        # make sure we have a ToolkitMolecule and if not, convert it
        if not isinstance(molecule, ToolkitMolecule):
            molecule = ToolkitMolecule.from_dynamic(molecule)

        # rdkit features only if installed
        rdkit_kwargs = (
            {"rdkit_mol": molecule.to_smiles()}
            if settings.postgres_rdkit_extension
            else {}
        )

        # Given a toolkit molecule object, this will return a database molecule
        # object, but will NOT save it to the database yet. The kwargs input
        # is only if you inherit from this class and add extra fields.
        molecule_dict = dict(
            molecule=molecule.to_sdf(),
            inchi=molecule.to_inchi(),
            inchi_key=molecule.to_inchi_key(),
            smiles=molecule.to_smiles(),
            num_atoms=molecule.num_atoms,
            num_stereocenters=molecule.num_stereocenters,
            num_rings=molecule.num_rings,
            num_h_acceptors=molecule.num_h_acceptors,
            num_h_donors=molecule.num_h_donors,
            log_p_rdkit=molecule.log_p_rdkit,
            tpsa_rdkit=molecule.tpsa_rdkit,
            synthetic_accessibility=molecule.synthetic_accessibility,
            functional_groups=molecule.get_fragments(),
            molecular_weight=molecule.molecular_weight,
            molecular_weight_exact=molecule.molecular_weight_exact,
            **rdkit_kwargs,
            **kwargs,  # this allows subclasses to add fields with ease
        )
        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return molecule_dict if as_dict else cls(**molecule_dict)

    def to_toolkit(self) -> ToolkitMolecule:
        """
        Converts the database object to toolkit Molecule object.
        """
        return ToolkitMolecule.from_sdf(self.molecule)

    @property
    def sdf_str(self) -> str:
        """
        Gives the sdf string of this molecule that can be rendered inside
        a django template <script> tag.

        We only have this as a property because we commonly access the SDF
        in django templates when using chemdoodle.
        """
        return self.to_toolkit().to_sdf().replace("\n", "\\n")

    @classmethod
    def populate_fingerprint_database(cls, empty_columns_only: bool = True):
        from django.db import connection  # local import bc of serialization bug

        query = (
            f"UPDATE    {cls._meta.db_table} "
            f"SET       fingerprint_morganbv = morganbv_fp(rdkit_mol)"
        )  # TODO: update_only: bool = False, limit: int = 50

        if empty_columns_only:
            query += " WHERE fingerprint_morganbv IS NULL"

        # BUG: injection risk here.
        #   https://docs.djangoproject.com/en/4.2/topics/db/sql/#passing-parameters-into-raw
        with connection.cursor() as cursor:
            cursor.execute(query)

    # -------------------------------------------------------------------------
