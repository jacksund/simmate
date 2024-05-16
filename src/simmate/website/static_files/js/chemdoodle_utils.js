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
// draws molecules
var doodle_molecule = function(sdf_str, canvas_id, size) { // TODO: switch order of args & match id naming below
    let myCanvas = new ChemDoodle.ViewerCanvas(canvas_id, size, size);
    // set this individually bc background color is important for some components
    myCanvas.styles.backgroundColor = undefined;
    // load the canvas + molecule
    let molecule = ChemDoodle.readMOL(sdf_str);
    myCanvas.loadMolecule(molecule);
    // I can't find how to remove the boarders... so I just remove the class
    var canvas = document.getElementById(canvas_id);
    canvas.classList.remove("ChemDoodleWebComponent");
};
// create a new sketching GUI
var create_doodle_sketcher = function(sketcher_id) {
    // when we init the SketcherCanvas, we store it in a global dict to access it elsewhere
    window.sketcherCanvases = window.sketcherCanvases || {}; // Ensure the dict exists where we store all sketchers
    window.sketcherCanvases[sketcher_id] = new ChemDoodle.SketcherCanvas(sketcher_id, 500, 300, {useServices:false, oneMolecule:true});
    var sketcher = window.sketcherCanvases[sketcher_id];
    // enables overlap clear widths, so that some depth is introduced to overlapping bonds
    sketcher.styles.bonds_clearOverlaps_2D = true;
    // sets the shape color to improve contrast when drawing figures
    sketcher.styles.shapes_color = 'c10000';
    // because we do not load any content, we need to repaint the sketcher, otherwise we would just see an empty area with the toolbar
    // however, you can instead use one of the Canvas.load... functions to pre-populate the canvas with content, then you don't need to call repaint
    sketcher.repaint();
};
// grab value from sketcher and paste it into a target unicorn input
var get_mol_from_sketcher = function(id, unicorn_view, unicorn_method) {
    var sketcher_id = "sketcher_" + id
    var textarea_id = "textarea_" + id
    // priority is given to the text input
    var user_input = document.getElementById(textarea_id);
    var molStr;
    if (user_input.value) {
        molStr = user_input.value;
    }
    // otherwise we pull what is in the sketcher and use that
    else {
        var sketcher = window.sketcherCanvases[sketcher_id];
        let mol = sketcher.getMolecule();
        molStr = ChemDoodle.writeMOL(mol); // or .writeMOLV3(mol); ...?
    }
    // and then we call unicorn to update the value
    Unicorn.call(unicorn_view, unicorn_method, JSON.stringify(molStr));
};
// unhide + update a canvas for doodle molecules
var refresh_doodle = function(id, new_sdf_str) {
    var canvas_id = "canvas_" + id
    // todo-- combine with doodle_molecule fxn above
    myCanvas = new ChemDoodle.ViewerCanvas(canvas_id);
    myCanvas.styles.backgroundColor = undefined;
    myCanvas.emptyMessage = 'No molecule loaded!';
    let molecule = ChemDoodle.readMOL(new_sdf_str);
    myCanvas.loadMolecule(molecule);
    // make canvas visible and remove boarder
    let canvas = document.getElementById(canvas_id);
    canvas.removeAttribute("hidden");
    canvas.classList.remove("ChemDoodleWebComponent");
    canvas.classList.add("p-0"); // bug-fix for aspect ratio
};