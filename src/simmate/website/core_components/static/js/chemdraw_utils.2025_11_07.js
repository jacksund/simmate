// API docs: https://usermanual.wiki/Pdf/ChemDraw20JS2017120API20Reference20Guide.1356440129.pdf

// Global dictionary to store sketcher instances
var sketchers = {};

// Creates a 2D molecule ChemDraw sketcher
function add_mol_sketcher(sketcher_id) {
    RevvitySignals.ChemdrawWebManager.attach({
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

// Detect whether a MOL string is "empty":
// - V2000: counts line has 0 atoms and 0 bonds (line with ... V2000)
// - V3000: "M  V30 COUNTS 0 0 ..."
function is_mol_empty(mol) {
    if (!mol || !mol.trim()) return true;

    var s = String(mol).replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    // V3000: look for COUNTS line
    var mV3000 = s.match(/^\s*M\s+V30\s+COUNTS\s+(\d+)\s+(\d+)/mi);
    if (mV3000) {
        var aV3 = parseInt(mV3000[1], 10);
        var bV3 = parseInt(mV3000[2], 10);
        if (!isNaN(aV3) && !isNaN(bV3) && aV3 === 0 && bV3 === 0) return true;
    }

    // V2000: find a line that ends with V2000 and parse first two counts (atoms, bonds)
    var lines = s.split('\n');
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (/\bV2000\b/.test(line)) {
            var trimmed = line.trim();
            // Regex approach
            var mV2000 = trimmed.match(/^(\d+)\s+(\d+)\b.*\bV2000\b/);
            if (mV2000) {
                var aV2 = parseInt(mV2000[1], 10);
                var bV2 = parseInt(mV2000[2], 10);
                if (!isNaN(aV2) && !isNaN(bV2) && aV2 === 0 && bV2 === 0) return true;
            }
            // Fixed-column fallback (columns 1-3: atoms, 4-6: bonds)
            if (line.length >= 6) {
                var aAlt = parseInt(line.substr(0, 3), 10);
                var bAlt = parseInt(line.substr(3, 3), 10);
                if (!isNaN(aAlt) && !isNaN(bAlt) && aAlt === 0 && bAlt === 0) return true;
            }
        }
    }

    return false;
}

// Retrieve MOL from a specific sketcher and write it to an input element
// If MOL is "empty", set the value to "None" instead.
function get_mol_from_sketcher(sketcher_id, input_element_id) {

    // Retrieve the sketcher from the global dictionary
    var sketcher = sketchers[sketcher_id];
    if (!sketcher) {
        console.error("Sketcher not found for sketcher_id: " + sketcher_id);
        return;
    }
    
    // Resolve the hidden input element
    var input_element = document.getElementById(input_element_id);
    if (!input_element) {
        console.error("Input element not found for: " + input_element_id);
        return;
    }
    
    // Pull out the molecule(s) as Mol string
    // we use Mol bc we want to keep orientation + enhanced stereochem
    sketcher.getMOL(function(mol, error) {
        if (error) {
            console.error("Error retrieving MOL: ", error);
            return;
        }

        // Decide output: null if empty, else MOL
        var newOut = is_mol_empty(mol) ? null : (mol || "");

        // Normalize to strings for the DOM
        var newOutStr = (newOut == null) ? "" : String(newOut);

        // Determine if current value is "null" (empty/stringless) and new is also "null"
        var oldValStr = input_element.value == null ? "" : String(input_element.value);
        var oldIsNull = (oldValStr === "");
        var newIsNull = (newOutStr === "");

        // Update the hidden input's value
        input_element.value = newOutStr;

        // Notify listeners (e.g., HTMX)
        // - Do NOT fire when both old and new are "null" (which occurs on sketcher init)
        try {
            if (!(oldIsNull && newIsNull)) {
                input_element.dispatchEvent(new Event('input', { bubbles: true }));
                input_element.dispatchEvent(new Event('change', { bubbles: true }));
            }
        } catch (e) {
            // Older browsers may not support Event constructor; ignore
        }
    });
}


// Enable auto-write of MOL to a hidden input on every sketcher change.
function enable_mol_autowrite(sketcher_id, input_element_id, options) {
    options = options || {};
    var debounceMs = typeof options.debounceMs === 'number' ? options.debounceMs : 50;
    var triggerInitial = options.triggerInitial !== false;

    function wire(sketcher) {
        var timer = null;
        sketcher.setContentChangedHandler(function (_event) {
            if (timer) {
                clearTimeout(timer);
            }
            if (debounceMs > 0) {
                timer = setTimeout(function () {
                    get_mol_from_sketcher(sketcher_id, input_element_id);
                }, debounceMs);
            } else {
                get_mol_from_sketcher(sketcher_id, input_element_id);
            }
        });

        if (triggerInitial) {
            get_mol_from_sketcher(sketcher_id, input_element_id);
        }
    }

    var sketcher = sketchers[sketcher_id];
    if (sketcher) {
        wire(sketcher);
        return;
    }

    // If called before the sketcher is attached, retry briefly.
    var tries = 40; // ~4s at 100ms
    var waiter = setInterval(function () {
        var sk = sketchers[sketcher_id];
        if (sk) {
            clearInterval(waiter);
            wire(sk);
        } else if (--tries <= 0) {
            clearInterval(waiter);
            console.error("enable_mol_autowrite: sketcher not found for sketcher_id:", sketcher_id);
        }
    }, 100);
}
