// API docs: https://usermanual.wiki/Pdf/ChemDraw20JS2017120API20Reference20Guide.1356440129.pdf

// Global dictionary to store sketcher instances
var sketchers = {};

// Creates a 2D molecule ChemDraw sketcher
function add_mol_sketcher(sketcher_id) {
    perkinelmer.ChemdrawWebManager.attach({
        id: sketcher_id,
        callback: function(chemdrawweb) {
            sketchers[sketcher_id] = chemdrawweb;  // Save the sketcher instance with its ID
        },
        errorCallback: function(error) {
            alert(error);  // Handle attachment failure
        },
        licenseUrl: ChemDrawLicenseURL, // global var set in site_base.html
    });
}

// Retrieve and handle MOL data from a specific sketcher
function get_mol_from_sketcher(sketcher_id, unicorn_view, unicorn_method) {

    // Retrieve the sketcher from the global dictionary
    var sketcher = sketchers[sketcher_id]; 
    
    // Pull out the molecule(s) as Mol strings (to keep orientation)
    if (sketcher) {
        sketcher.getMOL(function(mol, error) {
            if (error) {
                console.error("Error retrieving MOL: ", error);
            } else {
                // if success, then we call unicorn to update the value
                Unicorn.call(unicorn_view, unicorn_method, JSON.stringify(mol));
            }
        });
    } else {
        console.error("Sketcher not found for ID: " + sketcher_id);
    };
}
