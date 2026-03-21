
// Initialize RDKit module only once
let RDKitModule = null;  // Declare a global variable to store the initialized RDKit module

window.initRDKitModule().then(function (RDKit) {
    RDKitModule = RDKit;  // Store the initialized module in the global variable
}).catch((error) => {
    console.error("Failed to load RDKit.js", error);
});

// draws a molecule to svg
var add_mol_viewer = function (canvas_id, mol_str, width, height) {
    // Check if RDKit is initialized
    if (RDKitModule) {
        // load the canvas + molecule
        var mol = RDKitModule.get_mol(mol_str);
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
            'bondLineWidth': 2.5,
            'scaleBondWidth': true,
            'fixedBondLength': 50,  // bug: will this look different depending on monitor res?
            'additionalAtomLabelPadding': 0.1,
            // Dark Theme coloring orginally forked from... 
            // https://github.com/rdkit/rdkit-js/discussions/325#discussioncomment-7238704
            // 'atomColourPalette': {
            //     '-1':  [0.6, 0.6, 0.6],  // "dummy atoms" (R-groups, query atoms, etc.)
            //     0:   [0.7, 0.7, 0.7],  // unknown/unspecified element
            //     1:   [0.7, 0.7, 0.7],  // Hydrogen (H)
            //     6:   [0.7, 0.7, 0.7],  // Carbon (C)
            //     7:   [0.33, 0.41, 0.92], // Nitrogen (N) → blue
            //     8:   [1.0, 0.2, 0.2],    // Oxygen (O) → red
            //     9:   [0.2, 0.8, 0.8],    // Fluorine (F) → teal
            //     15:  [1.0, 0.5, 0.0],    // Phosphorus (P) → orange
            //     16:  [0.8, 0.8, 0.0],    // Sulfur (S) → yellow
            //     17:  [0.0, 0.802, 0.0],  // Chlorine (Cl) → green
            //     35:  [0.71, 0.4, 0.07],  // Bromine (Br) → brown
            //     53:  [0.89, 0.004, 1],   // Iodine (I) → purple/violet
            //     201: [0.68, 0.85, 0.90], // Pseudo-atom/other (RDKit special, used in queries)
            // },
         };
        var svg = mol.get_svg_with_highlights(JSON.stringify(rdkit_styling));
        mol_canvas.innerHTML = svg;
        
        // sometimes the div starts as hidden and we unhide it to show the mol
        mol_canvas.removeAttribute("hidden");
        
        // if we are drawing from a div that was originally a sketcher, then
        // we need to clear its styling
        mol_canvas.style.height = '';
        mol_canvas.style.width = '';
    } else {
        // RDKit is not initialized yet.
        // Poll every 100ms until RDKit is initialized
        var interval = setInterval(function () {
            if (RDKitModule) {
                add_mol_viewer(canvas_id, mol_str, width, height);  // Reattempt molecule rendering
                clearInterval(interval);
            }
        }, 100);
    };
};


// unsets the molecule SVG and rehides the canvas
var remove_mol_viewer = function(canvas_id) {
    var mol_canvas = document.getElementById(canvas_id);
    mol_canvas.hidden = true;
    mol_canvas.innerHTML = '';
};
