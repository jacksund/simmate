
var add_mol_viewer = function (canvas_id, mol_str, width, height) {
    window
        .initRDKitModule()
        .then(function (RDKit) {

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
                'width': width,
                'height': height,
                'fixedBondLength': 50,  // bug: will this look different depending on monitor res?
             };
            var svg = mol.get_svg_with_highlights(JSON.stringify(rdkit_styling));
            mol_canvas.innerHTML = svg;
            
            // sometimes the div starts as hidden and we unhide it to show the mol
            mol_canvas.removeAttribute("hidden");
            mol_canvas.style.height = '';
            mol_canvas.style.width = '';
        })
        .catch((error) => {
            console.error("Failed to load RDKit.js", error);
        });
};


// unsets the molecule and rehides the canvas
//var remove_mol_viewer = function(id, new_sdf_str) {
//    var canvas_id = "canvas_" + id
//   // remove the current mol
//    refresh_doodle(id, "");
//    // hide the canvas
//    document.getElementById(canvas_id).hidden = true;
// };
