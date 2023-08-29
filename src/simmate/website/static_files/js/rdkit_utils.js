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
// A custom function to help with drawing molecules
var add_mol_viewer = function (mol_str, canvas_id, size) {
    // load the canvas + molecule
    var mol = RDKit.get_mol(mol_str);
    var canvas = document.getElementById(canvas_id);

    // reset the size of the canvas
    canvas.width = size;
    canvas.height = size;

    // Normally you draw the molecule with this method,
    // but we want extra styling options, so we use the
    // "draw_to_canvas_with_highlights" instead:
    //     mol.draw_to_canvas(canvas, -1, -1);
    // styling options (e.g. clear background)
    var mdetails = {};
    mdetails['backgroundColour']=[0.0, 0.0, 0.0, 0.0];
    mol.draw_to_canvas_with_highlights(
        canvas, 
        JSON.stringify(mdetails),
    );
};