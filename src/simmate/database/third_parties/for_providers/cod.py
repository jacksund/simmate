# -*- coding: utf-8 -*-


"""

> :warning: This file is only for use by the Simmate team. Users should instead
access data via the load_remote_archive method.

This file is for pulling COD data into the Simmate database. 

The COD let's you download all of their data as a zip file 
[here](http://www.crystallography.net/archives/). While they do have a
REST API, it looks like they prefer you to use the zip file if you want all structures
and metadata. This is a big download even when compressed (18GB), so it's a slow
process -- but more importantly a stable one. For future reference though, the REST
API is outlined [here](https://wiki.crystallography.net/RESTful_API/).

Once downloaded, all of the cif files are organized into folders based on their first
few numbers -- for example, the cif 1234567 would be in folder /cif/1/23/45/1234567.cif
It's an odd way of storing the files, but we just need to script open all of the folders.
Note that some folders also don't have any cifs in them! There is also extra data
in each cif file -- such as the doi of the paper it came from.

There looks to be a lot of problematic cif files in the COD, but it's not worth parsing
through all of these. Instead, I simply try to load the cif file into a pymatgen
Structure object, and if it fails, I just move on. I'm slowly adding functionality
to account for these problematic cif files though.

"""

import os

from pymatgen.io.cif import CifParser

from simmate.configuration.dask import batch_submit
from simmate.database.third_parties import CodStructure


def load_all_structures(
    base_directory: str = "cod/cif/",
    only_add_new_cifs: bool = True,
    batch_size: int = 15000,
    batch_timeout: float = 30 * 60,
):
    """
    Only use this function if you are part of the Simmate dev team!

    Loads all structures directly for the COD database into the local
    Simmate database. There are 480,160 structures as of 2022-02-18.
    Because of problematic cifs, only 471,664 (98.2%) are imported into
    the Simmate database successfully.

    Make sure you have downloaded the
    [COD archive]([here](http://www.crystallography.net/archives/))
    and have it upacked to match your base_directory input.
    """

    # We need to look at all the folders that have numbered-names (1,2,3..,9). and
    # grab the folder inside that are also numbers. This continues until we find cif
    # files that we can pull structures from. Note the name of the cif file is also
    # the cod-id.
    all_cifs = []
    for folder_name1 in os.listdir(base_directory):
        # skip if the folder name isn't a number
        if not folder_name1.isnumeric():
            continue
        # otherwise go through the folders inside of this one
        for folder_name2 in os.listdir(os.path.join(base_directory, folder_name1)):
            # and then one more level until we hit the cifs!
            for folder_name3 in os.listdir(
                os.path.join(base_directory, folder_name1, folder_name2)
            ):
                # we now have all the foldernames we need. Let's record the full path
                folder_path = os.path.join(
                    base_directory, folder_name1, folder_name2, folder_name3
                )
                # now go through each cif file in this directory
                for cif_filename in os.listdir(folder_path):
                    # construct the full path to the file we are after
                    cif_filepath = os.path.join(folder_path, cif_filename)
                    all_cifs.append(cif_filepath)

    # Sometimes we are retrying this function call from a previously failed
    # run. In that case, we only want to run the cifs that haven't been loaded
    # yet. We iterate throught the cif ids and select which ones aren't in
    # the database yet. This takes roughly 2 min but saves a lot of time accross
    # runs.
    if only_add_new_cifs:
        print("Removing existing cifs from to-do list...")
        new_cifs = []
        from tqdm import tqdm

        for cif_filepath in tqdm(all_cifs):
            cif_id = "cod-" + os.path.basename(cif_filepath).split(".")[0]
            if not CodStructure.objects.filter(id=cif_id).exists():
                new_cifs.append(cif_filepath)

        # replace our all_cifs with this updated list
        all_cifs = new_cifs

    # We run this function in parallel using Dask.
    # Dask seems to be unstable when we submit too much at once, so we chunk
    # our submissions and wait for each to finished before submitting more.
    # We only wait for all futures to complete in 30 min, and beyond that
    # point, cancel any remaining. 30 min is plenty for a batch of
    # 15,000 cifs. If this limit is ever hit, it's typically because a
    # single cif is taking >15min and is problematic.
    batch_submit(
        function=load_single_cif,
        args_list=all_cifs,
        batch_size=batch_size,
        batch_timeout=batch_timeout,
    )


def load_single_cif(cif_filepath: str):
    """
    Loads a single COD cif into the Simmate database.

    You typically shouldn't call this function directly. We make this a
    separate function to allow parallelization in `load_all_structures`.
    """

    # Load the structure and extra data from the cif file.
    # Note, some occupancies are not scaled to sum to 1. For
    # example, a disordered site may have [Ca:1, Sr:1] instead of
    # [Ca:0.5, Sr:0.5]. By setting our occupancy tolerance to
    # infinity, we let pymatgen scale the occupancies so they sum to 1.
    cif = CifParser(
        cif_filepath,
        occupancy_tolerance=float("inf"),
    )

    # pull out the structure
    # note we use CifParser.get_structures instead of
    # Structure.from_file because we wanted the extra data too.
    # The COD has a lot of structures that aren't formatted properly
    # and various errors are thrown throughout the loading process.
    # for now, I just skip the ones that give issues.
    # !!! I should take a closer look at failed cifs in the future.
    try:
        structure = cif.get_structures()[0]
    except ValueError as error:
        # There is a common error where no structure is found, but
        # if this error ends up being something different, we should
        # make sure it's raised for visibility.
        if error.args != ("Invalid cif file with no structures!",):
            raise error
        # otherwise exit
        return

    if (
        "Structure has implicit hydrogens defined, parsed structure"
        " unlikely to be suitable for use in calculations unless"
        " hydrogens added." in cif.warnings
    ):
        has_implicit_hydrogens = True
    else:
        has_implicit_hydrogens = False

    # Compile all of our data into a dictionary
    entry_dict = {
        # the split removes ".cif" from each file name and
        # the remaining number is the id
        "id": "cod-" + os.path.basename(cif_filepath).split(".")[0],
        "structure": structure,
        "is_ordered": structure.is_ordered,
        "has_implicit_hydrogens": has_implicit_hydrogens,
        # OPTMIZE: right now I use the title of the paper,
        # but I would much rather use the DOI as it's shorter
        # and more useful. But a lot of cifs are missing the
        # _journal_paper_doi... This should be fixed.
        # "paper_title": data[key].get("_publ_section_title"),
    }

    # now convert the entry to a database object
    structure_db = CodStructure.from_toolkit(**entry_dict)

    # and save it to our database!
    structure_db.save()


# --------------------------------------------------------------------------------------

# This a list of all CIF keywords that are seen in the COD database. Here, I go
# through all of them and decide which to remove and which to store. The removed
# keywords are commented out and I add an explanation as to why. For determining
# the meaning of each keyword, look here:
#   https://www.iucr.org/resources/cif/dictionaries/search
cif_keywords = [
    # I'm removing _atom_rho_multipole_* and _atom_local_axes_* keywords for now.
    # These are composed of electron density information and I should consider
    # adding a separate django model to store this information.
    # https://www.iucr.org/__data/iucr/cifdic_html/1/cif_rho.dic/index.html
    # "_atom_local_axes_atom0",
    # "_atom_local_axes_atom1",
    # "_atom_local_axes_atom2",
    # "_atom_local_axes_atom_label",
    # "_atom_local_axes_ax1",
    # "_atom_local_axes_ax2",
    # "_atom_rho_multipole_atom_label",
    # "_atom_rho_multipole_coeff_P00",
    # "_atom_rho_multipole_coeff_P1-1",
    # "_atom_rho_multipole_coeff_P10",
    # "_atom_rho_multipole_coeff_P11",
    # "_atom_rho_multipole_coeff_P2-1",
    # "_atom_rho_multipole_coeff_P2-2",
    # "_atom_rho_multipole_coeff_P20",
    # "_atom_rho_multipole_coeff_P21",
    # "_atom_rho_multipole_coeff_P22",
    # "_atom_rho_multipole_coeff_P3-1",
    # "_atom_rho_multipole_coeff_P3-2",
    # "_atom_rho_multipole_coeff_P3-3",
    # "_atom_rho_multipole_coeff_P30",
    # "_atom_rho_multipole_coeff_P31",
    # "_atom_rho_multipole_coeff_P32",
    # "_atom_rho_multipole_coeff_P33",
    # "_atom_rho_multipole_coeff_P4-1",
    # "_atom_rho_multipole_coeff_P4-2",
    # "_atom_rho_multipole_coeff_P4-3",
    # "_atom_rho_multipole_coeff_P4-4",
    # "_atom_rho_multipole_coeff_P40",
    # "_atom_rho_multipole_coeff_P41",
    # "_atom_rho_multipole_coeff_P42",
    # "_atom_rho_multipole_coeff_P43",
    # "_atom_rho_multipole_coeff_P44",
    # "_atom_rho_multipole_coeff_Pv",
    # "_atom_rho_multipole_kappa",
    # "_atom_rho_multipole_kappa_prime0",
    # "_atom_rho_multipole_kappa_prime1",
    # "_atom_rho_multipole_kappa_prime2",
    # "_atom_rho_multipole_kappa_prime3",
    # "_atom_rho_multipole_kappa_prime4",
    #
    #
    # These _atom_* keywords are part of the core library. The main data will
    # stored in the pymatgen structure we pull out, but I may need to return to
    # some keywords. See here:
    #   https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/index.html
    # "_atom_site_B_iso_or_equiv",
    # "_atom_site_U_iso_or_equiv",
    # "_atom_site_Wyckoff_symbol",
    # "_atom_site_adp_type",
    # "_atom_site_aniso_U_11",
    # "_atom_site_aniso_U_12",
    # "_atom_site_aniso_U_13",
    # "_atom_site_aniso_U_22",
    # "_atom_site_aniso_U_23",
    # "_atom_site_aniso_U_33",
    # "_atom_site_aniso_label",
    # "_atom_site_aniso_type_symbol",
    # "_atom_site_attached_hydrogens",
    # "_atom_site_calc_flag",
    # "_atom_site_disorder_assembly",
    # "_atom_site_disorder_group",
    # "_atom_site_fract_x",
    # "_atom_site_fract_y",
    # "_atom_site_fract_z",
    # "_atom_site_label",
    # "_atom_site_occupancy",
    # "_atom_site_refinement_flags",
    # "_atom_site_refinement_flags_adp",
    # "_atom_site_refinement_flags_occupancy",
    # "_atom_site_refinement_flags_posn",
    # "_atom_site_site_symmetry_multiplicity",
    # "_atom_site_site_symmetry_order",
    # "_atom_site_symmetry_multiplicity",
    # "_atom_site_thermal_displace_type",
    # "_atom_site_type_symbol",
    # "_atom_sites_solution_hydrogens",
    # "_atom_sites_solution_primary",
    # "_atom_sites_solution_secondary",
    # "_atom_type_description",
    # "_atom_type_oxidation_number",
    # "_atom_type_scat_dispersion_imag",
    # "_atom_type_scat_dispersion_real",
    # "_atom_type_scat_source",
    # "_atom_type_symbol",
    #
    #
    # The _audit_* keywords hold information about the creation and subsequent
    # updating of the cif file.
    # "_audit_block_code",
    # "_audit_conform_dict_location",
    # "_audit_conform_dict_name",
    # "_audit_conform_dict_version",
    # "_audit_creation_date",
    # "_audit_creation_method",
    # "_audit_update_record",
    #
    #
    # These keywords are simply the lattice, which are stored via pymatgen.
    # "_cell_angle_alpha",
    # "_cell_angle_beta",
    # "_cell_angle_gamma",
    # "_cell_formula_units_Z",
    # "_cell_length_a",
    # "_cell_length_b",
    # "_cell_length_c",
    # "_cell_volume",
    #
    #
    # This includes important experimental information for how the lattice was
    # determined.
    # "_cell_measurement_reflns_used",
    # "_cell_measurement_temperature",
    # "_cell_measurement_theta_max",
    # "_cell_measurement_theta_min",
    # "_cell_measurement_wavelength",
    #
    #
    # This is simple composition information that we get from the pymatgen structure
    # anyways.
    # "_chemical_formula_analytical",
    # "_chemical_formula_iupac",
    # "_chemical_formula_moiety",
    # "_chemical_formula_structural",
    # "_chemical_formula_sum",
    # "_chemical_formula_weight",
    #
    #
    # Important information for how the compsition was determined and how the aquired
    # same was aquired.
    # "_chemical_absolute_configuration",
    # "_chemical_compound_source",
    #
    #
    # Important information about the physical properties of the compound.
    # "_chemical_melting_point",
    # "_chemical_melting_point_gt",
    # "_chemical_melting_point_lt",
    # "_chemical_properties_physical",
    # "_chemical_temperature_decomposition_gt",
    #
    #
    # I remove naming for now, but I may want to re-add these for the mineral
    # names.
    # "_chemical_name_common",
    # "_chemical_name_mineral",
    # "_chemical_name_systematic",
    #
    #
    # These properties aren't shown on https://www.iucr.org/ so I remove them.
    # "_chemical_oxdiff_formula",
    # "_chemical_oxdiff_usercomment",
    #
    #
    # Important COD information. Some of this I remove for not being particularly
    # useful in a secondary database.
    "_cod_data_source_block",
    "_cod_data_source_file",
    "_cod_database_code",
    "_cod_database_fobs_code",
    "_cod_depositor_comments",
    "_cod_duplicate_entry",
    # "_cod_original_cell_volume",
    # "_cod_original_formula_sum",
    # "_cod_original_sg_symbol_H-M",
    # "_cod_original_sg_symbol_Hall",
    "_cod_related_entry_code",
    "_cod_related_entry_database",
    "_cod_related_entry_id",
    "_cod_struct_determination_method",
    #
    #
    # The _computing_* keywords contain information about the computer software
    # used to perform the analysis.
    # "_computing_cell_refinement",
    # "_computing_data_collection",
    # "_computing_data_reduction",
    # "_computing_molecular_graphics",
    # "_computing_publication_material",
    # "_computing_structure_refinement",
    # "_computing_structure_solution",
    #
    #
    # Important information about the experimental conditions, where _diffrn_*
    # relate to DURING diffraction, while _exptl_* are BEFORE diffraction.
    # There is a lot of information here, including the spectrum aquired. This
    # is worth putting into a separate django Model to store.
    # "_diffrn_ambient_environment",
    # "_diffrn_ambient_pressure",
    # "_diffrn_ambient_temperature",
    # "_diffrn_detector",
    # "_diffrn_detector_area_resol_mean",
    # "_diffrn_detector_type",
    # "_diffrn_measured_fraction_theta_full",
    # "_diffrn_measured_fraction_theta_max",
    # "_diffrn_measurement_details",
    # "_diffrn_measurement_device",
    # "_diffrn_measurement_device_details",
    # "_diffrn_measurement_device_type",
    # "_diffrn_measurement_method",
    # "_diffrn_measurement_specimen_support",
    # "_diffrn_orient_matrix_UB_11",
    # "_diffrn_orient_matrix_UB_12",
    # "_diffrn_orient_matrix_UB_13",
    # "_diffrn_orient_matrix_UB_21",
    # "_diffrn_orient_matrix_UB_22",
    # "_diffrn_orient_matrix_UB_23",
    # "_diffrn_orient_matrix_UB_31",
    # "_diffrn_orient_matrix_UB_32",
    # "_diffrn_orient_matrix_UB_33",
    # "_diffrn_orient_matrix_type",
    # "_diffrn_radiation_collimation",
    # "_diffrn_radiation_detector",
    # "_diffrn_radiation_monochromator",
    # "_diffrn_radiation_probe",
    # "_diffrn_radiation_source",
    # "_diffrn_radiation_type",
    # "_diffrn_radiation_wavelength",
    # "_diffrn_radiation_wavelength_wt",
    # "_diffrn_radiation_xray_symbol",
    # "_diffrn_refln_index_h",
    # "_diffrn_refln_index_k",
    # "_diffrn_refln_index_l",
    # "_diffrn_refln_intensity_net",
    # "_diffrn_refln_intensity_u",
    # "_diffrn_refln_scale_group_code",
    # "_diffrn_reflns_Laue_measured_fraction_full",
    # "_diffrn_reflns_Laue_measured_fraction_max",
    # "_diffrn_reflns_av_R_equivalents",
    # "_diffrn_reflns_av_sigmaI/netI",
    # "_diffrn_reflns_av_unetI/netI",
    # "_diffrn_reflns_laue_measured_fraction_full",
    # "_diffrn_reflns_laue_measured_fraction_max",
    # "_diffrn_reflns_limit_h_max",
    # "_diffrn_reflns_limit_h_min",
    # "_diffrn_reflns_limit_k_max",
    # "_diffrn_reflns_limit_k_min",
    # "_diffrn_reflns_limit_l_max",
    # "_diffrn_reflns_limit_l_min",
    # "_diffrn_reflns_number",
    # "_diffrn_reflns_point_group_measured_fraction_full",
    # "_diffrn_reflns_point_group_measured_fraction_max",
    # "_diffrn_reflns_reduction_process",
    # "_diffrn_reflns_theta_full",
    # "_diffrn_reflns_theta_max",
    # "_diffrn_reflns_theta_min",
    # "_diffrn_source",
    # "_diffrn_source_current",
    # "_diffrn_source_power",
    # "_diffrn_source_target",
    # "_diffrn_source_type",
    # "_diffrn_source_voltage",
    # "_diffrn_standards_decay_%",
    # "_diffrn_standards_interval_count",
    # "_diffrn_standards_interval_time",
    # "_diffrn_standards_number",
    # "_exptl_absorpt_coefficient_mu",
    # "_exptl_absorpt_correction_T_max",
    # "_exptl_absorpt_correction_T_min",
    # "_exptl_absorpt_correction_type",
    # "_exptl_absorpt_process_details",
    # "_exptl_crystal_F_000",
    # "_exptl_crystal_colour",
    # "_exptl_crystal_colour_lustre",
    # "_exptl_crystal_colour_modifier",
    # "_exptl_crystal_colour_primary",
    # "_exptl_crystal_density_diffrn",
    # "_exptl_crystal_density_meas",
    # "_exptl_crystal_density_method",
    # "_exptl_crystal_description",
    # "_exptl_crystal_face_index_h",
    # "_exptl_crystal_face_index_k",
    # "_exptl_crystal_face_index_l",
    # "_exptl_crystal_face_perp_dist",
    # "_exptl_crystal_preparation",
    # "_exptl_crystal_pressure_history",
    # "_exptl_crystal_recrystallization_method",
    # "_exptl_crystal_size_max",
    # "_exptl_crystal_size_mid",
    # "_exptl_crystal_size_min",
    # "_exptl_crystal_size_rad",
    # "_exptl_crystal_thermal_history",
    # "_exptl_oxdiff_crystal_face_indexfrac_h",
    # "_exptl_oxdiff_crystal_face_indexfrac_k",
    # "_exptl_oxdiff_crystal_face_indexfrac_l",
    # "_exptl_oxdiff_crystal_face_x",
    # "_exptl_oxdiff_crystal_face_y",
    # "_exptl_oxdiff_crystal_face_z",
    # "_exptl_transmission_factor_max",
    # "_exptl_transmission_factor_min",
    #
    #
    # All _geom_* keywords are redundant and can be calculated by other methods.
    # Read more here:
    #   https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Cgeom.html
    # "_geom_angle",
    # "_geom_angle_atom_site_label_1",
    # "_geom_angle_atom_site_label_2",
    # "_geom_angle_atom_site_label_3",
    # "_geom_angle_publ_flag",
    # "_geom_angle_site_symmetry_1",
    # "_geom_angle_site_symmetry_2",
    # "_geom_angle_site_symmetry_3",
    # "_geom_bond_atom_site_label_1",
    # "_geom_bond_atom_site_label_2",
    # "_geom_bond_distance",
    # "_geom_bond_publ_flag",
    # "_geom_bond_site_symmetry_1",
    # "_geom_bond_site_symmetry_2",
    # "_geom_contact_atom_site_label_1",
    # "_geom_contact_atom_site_label_2",
    # "_geom_contact_distance",
    # "_geom_contact_publ_flag",
    # "_geom_contact_site_symmetry_2",
    # "_geom_hbond_angle_DHA",
    # "_geom_hbond_atom_site_label_A",
    # "_geom_hbond_atom_site_label_D",
    # "_geom_hbond_atom_site_label_H",
    # "_geom_hbond_distance_DA",
    # "_geom_hbond_distance_DH",
    # "_geom_hbond_distance_HA",
    # "_geom_hbond_publ_flag",
    # "_geom_hbond_site_symmetry_A",
    # "_geom_torsion",
    # "_geom_torsion_atom_site_label_1",
    # "_geom_torsion_atom_site_label_2",
    # "_geom_torsion_atom_site_label_3",
    # "_geom_torsion_atom_site_label_4",
    # "_geom_torsion_publ_flag",
    # "_geom_torsion_site_symmetry_1",
    # "_geom_torsion_site_symmetry_2",
    # "_geom_torsion_site_symmetry_3",
    # "_geom_torsion_site_symmetry_4",
    #
    #
    # Important information about where the data was originally published. Ideally,
    # I would only ever want to store the doi, but it looks like many COD structures
    # are missing this entry.
    "_journal_coden_ASTM",
    "_journal_issue",
    "_journal_name_full",
    "_journal_page_first",
    "_journal_page_last",
    "_journal_paper_doi",
    "_journal_volume",
    "_journal_year",
    "_publ_author_name",
    "_publ_contact_author",
    "_publ_contact_author_address",
    "_publ_contact_author_email",
    "_publ_contact_author_name",
    "_publ_contact_author_phone",
    "_publ_section_title",
    #
    #
    # These keywords should be clumped in with _computing_* ones because they
    # are each for a specific software and the details on its setup.
    # "_olex2_date_sample_data_collection",
    # "_olex2_date_sample_submission",
    # "_olex2_diffrn_ambient_temperature_device",
    # "_olex2_exptl_crystal_mounting_method",
    # "_olex2_refinement_description",
    # "_olex2_submission_original_sample_id",
    # "_olex2_submission_special_instructions",
    # "_shelx_estimated_absorpt_t_max",
    # "_shelx_estimated_absorpt_t_min",
    # "_shelx_fab_checksum",
    # "_shelx_fab_file",
    # "_shelx_hkl_checksum",
    # "_shelx_hkl_file",
    # "_shelx_res_checksum",
    # "_shelx_res_file",
    # "_shelx_shelxl_version_number",
    # "_shelx_space_group_comment",
    # "_shelxl_hkl_file",
    # "_shelxl_res_file",
    # "_shelxl_version_number",
    # "_smtbx_masks_void_average_x",
    # "_smtbx_masks_void_average_y",
    # "_smtbx_masks_void_average_z",
    # "_smtbx_masks_void_content",
    # "_smtbx_masks_void_count_electrons",
    # "_smtbx_masks_void_nr",
    # "_smtbx_masks_void_probe_radius",
    # "_smtbx_masks_void_truncation_radius",
    # "_smtbx_masks_void_volume",
    # "_platon_squeeze_details",
    # "_platon_squeeze_void_average_x",
    # "_platon_squeeze_void_average_y",
    # "_platon_squeeze_void_average_z",
    # "_platon_squeeze_void_content",
    # "_platon_squeeze_void_count_electrons",
    # "_platon_squeeze_void_nr",
    # "_platon_squeeze_void_probe_radius",
    # "_platon_squeeze_void_volume",
    # "_iucr_refine_instructions_details",
    # "_iucr_refine_reflections_details",
    #
    #
    # !!! unknown
    # "_oxdiff_exptl_absorpt_empirical_details",
    # "_oxdiff_exptl_absorpt_empirical_full_max",
    # "_oxdiff_exptl_absorpt_empirical_full_min",
    #
    #
    # All _pd_* keywords contain information about powder diffraction. It may
    # be worth combining with the _diffrn_* section. Read more here:
    #   https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/index.html
    # "_pd_char_colour",
    # "_pd_meas_2theta_range_inc",
    # "_pd_meas_2theta_range_max",
    # "_pd_meas_2theta_range_min",
    # "_pd_meas_scan_method",
    # "_pd_proc_ls_pref_orient_corr",
    # "_pd_proc_ls_prof_R_factor",
    # "_pd_proc_ls_prof_wR_expected",
    # "_pd_proc_ls_prof_wR_factor",
    # "_pd_proc_ls_profile_function",
    # "_pd_proc_number_of_points",
    # "_pd_spec_mount_mode",
    #
    #
    # Important information about the structure refinement and how it was done.
    # Consider joining with software details (_computing_*)
    # "_refine_diff_density_max",
    # "_refine_diff_density_min",
    # "_refine_diff_density_rms",
    # "_refine_ls_R_I_factor",
    # "_refine_ls_R_factor_all",
    # "_refine_ls_R_factor_gt",
    # "_refine_ls_R_factor_obs",
    # "_refine_ls_abs_structure_Flack",
    # "_refine_ls_abs_structure_details",
    # "_refine_ls_coordinate_system",
    # "_refine_ls_extinction_coef",
    # "_refine_ls_extinction_expression",
    # "_refine_ls_extinction_method",
    # "_refine_ls_goodness_of_fit_all",
    # "_refine_ls_goodness_of_fit_gt",
    # "_refine_ls_goodness_of_fit_ref",
    # "_refine_ls_hydrogen_treatment",
    # "_refine_ls_matrix_type",
    # "_refine_ls_number_constraints",
    # "_refine_ls_number_parameters",
    # "_refine_ls_number_reflns",
    # "_refine_ls_number_restraints",
    # "_refine_ls_restrained_S_all",
    # "_refine_ls_shift/su_max",
    # "_refine_ls_shift/su_mean",
    # "_refine_ls_structure_factor_coef",
    # "_refine_ls_svd_threshold",
    # "_refine_ls_wR_factor_all",
    # "_refine_ls_wR_factor_gt",
    # "_refine_ls_wR_factor_obs",
    # "_refine_ls_wR_factor_ref",
    # "_refine_ls_weighting_details",
    # "_refine_ls_weighting_scheme",
    #
    #
    # !!! How do these differ from _diffrn_refln_* ?? Consider joining this data
    # with that section.
    # "_refln_F_squared_meas",
    # "_refln_F_squared_sigma",
    # "_refln_index_h",
    # "_refln_index_k",
    # "_refln_index_l",
    # "_refln_scale_group_code",
    # "_reflns.d_resolution_high",
    # "_reflns.d_resolution_low",
    # "_reflns_Friedel_coverage",
    # "_reflns_Friedel_fraction_full",
    # "_reflns_Friedel_fraction_max",
    # "_reflns_number_gt",
    # "_reflns_number_total",
    # "_reflns_odcompleteness_completeness",
    # "_reflns_odcompleteness_iscentric",
    # "_reflns_odcompleteness_theta",
    # "_reflns_threshold_expression",
    #
    #
    # This is extra information that can be reattained in pymatgen.
    # "_space_group_IT_number",
    # "_space_group_crystal_system",
    # "_space_group_name_H-M_alt",
    # "_space_group_name_Hall",
    # "_space_group_symop_id",
    # "_space_group_symop_operation_xyz",
    # "_symmetry_Int_Tables_number",
    # "_symmetry_cell_setting",
    # "_symmetry_equiv_pos_as_xyz",
    # "_symmetry_equiv_pos_site_id",
    # "_symmetry_space_group_name_H-M",
    # "_symmetry_space_group_name_Hall",
    #
    #
    # !!! unknown keywords
    # "_twin_individual_id",
    # "_twin_individual_mass_fraction_refined",
    # "_citation_journal_id_ASTM",
    # "_database_code_amcsd",
]
