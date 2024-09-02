//ChemDoodle.DEFAULT_STYLES.
ChemDoodle.DEFAULT_STYLES.bondLength_2D = 40;
ChemDoodle.DEFAULT_STYLES.bonds_width_2D = 1.6;
ChemDoodle.DEFAULT_STYLES.bonds_saturationWidthAbs_2D = 5.2;
ChemDoodle.DEFAULT_STYLES.bonds_hashSpacing_2D = 5;
ChemDoodle.DEFAULT_STYLES.atoms_font_size_2D = 20;
ChemDoodle.DEFAULT_STYLES.atoms_font_families_2D = ['Helvetica', 'Arial', 'sans-serif'];
ChemDoodle.DEFAULT_STYLES.atoms_displayTerminalCarbonLabels_2D = false;
ChemDoodle.DEFAULT_STYLES.atoms_useJMOLColors = true;
// changes the default JMol color of hydrogen to black so it appears on white backgrounds
ChemDoodle.ELEMENT['H'].jmolColor = 'black';
// darkens the default JMol color of sulfur so it appears on white backgrounds
ChemDoodle.ELEMENT['S'].jmolColor = '#B9A130';
// function to grab value from sketcher and paste it into a target unicorn input
var get_mol_from_sketcher = function (
    sketcher,
    textarea_id,
    unicorn_view,
    unicorn_method,
) {
    // priority is given to the text input
    var user_input = document.getElementById(textarea_id);
    var molStr;
    if (user_input.value) {
        molStr = user_input.value;
    }
    // otherwise we pull what is in the sketcher and use that
    else {
        let mol = sketcher.getMolecule();
        molStr = ChemDoodle.writeMOL(mol); // or .writeMOLV3(mol); ...?
    }
    // and then we call unicorn to update the value
    Unicorn.call(unicorn_view, unicorn_method, JSON.stringify(molStr));
};
