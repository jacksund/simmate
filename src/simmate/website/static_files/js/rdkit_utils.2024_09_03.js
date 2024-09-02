// BUG: I thought this would go first... but it looks like this runs AFTER the page loaded...
// Instantiate the WASM module. The inline script below could live elsewhere inside your application code.
// window
//     .initRDKitModule()
//     .then(function (RDKit) {
//         console.log("RDKit version: " + RDKit.version());
//         window.RDKit = RDKit;
//         /**
//          * The RDKit module is now loaded.
//          * You can use it anywhere.
//          */
//     })
//     .catch(() => {
//         // handle loading errors here...
//     });
// TODO: add a rdkitjs_wrapper function to help remove boilerplate below

// A custom function to help with drawing molecules
var add_mol_viewer_base = function (mol_str, canvas_id, size, RDKit) {

        // load the canvas + molecule
        var mol = RDKit.get_mol(mol_str);
        var mol_canvas = document.getElementById(canvas_id);
        
        // Normally you draw the molecule with this method,
        // but we want extra styling options, so we use the
        // "get_svg_with_highlights" instead:
        //     mol.get_svg();
        // styling options (e.g. clear background)
        var rdkit_styling = { 
            'backgroundColour': [0.0, 0.0, 0.0, 0.0],
            // these set the max bounds, so if the molecule is too large, its
            // largest dimension will be shrunk to meet the limits here
            'width': size,
            'height': size,
         };
        var svg = mol.get_svg_with_highlights(JSON.stringify(rdkit_styling));
        mol_canvas.innerHTML = svg;
};
// BUG-FIX VERSIONS OF THE FUCTIONS
var add_mol_viewer = function (mol_str, canvas_id, size) {
    window
        .initRDKitModule()
        .then(function (RDKit) {
            add_mol_viewer_base(mol_str, canvas_id, size, RDKit);
        })
        .catch((error) => {
            console.error("Failed to load RDKit.js", error);
        });
};
var refresh_mol_viewer = function (canvas_id, new_sdf_str) {
    console.log("refresh_mol_viewer isn't implemented yet!")
    // // todo-- combine with add_mol_viewer fxn above
    // myCanvas = new ChemDoodle.ViewerCanvas(canvas_id);
    // myCanvas.styles.backgroundColor = undefined;
    // myCanvas.emptyMessage = 'No molecule loaded!';
    // let molecule = ChemDoodle.readMOL(new_sdf_str);
    // myCanvas.loadMolecule(molecule);
    // // make canvas visible and remove boarder
    // let canvas = document.getElementById(canvas_id);
    // canvas.removeAttribute("hidden");
    // canvas.classList.remove("ChemDoodleWebComponent");
    // canvas.classList.add("p-0"); // bug-fix for aspect ratio
};