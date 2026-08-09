// Global dictionary to store sketcher instances
var sketchers = {};

// Creates a 2D molecule Ketcher sketcher
function add_mol_sketcher(sketcher_id) {
    var container = document.getElementById(sketcher_id);
    var iframe = document.createElement('iframe');
    iframe.id = sketcher_id + "-iframe";
    
    // We point to a local version of Ketcher. 
    // This is downloaded automatically by 'simmate run-server'
    iframe.src = "/static/ketcher/index.html";
    
    iframe.width = "100%";
    iframe.height = "100%";
    iframe.style.border = "none";
    container.appendChild(iframe);
    
    // Periodically check for ketcher in iframe contentWindow
    // Ketcher becomes available on the window object once the iframe is loaded.
    var checkInterval = setInterval(function() {
        if (iframe.contentWindow && iframe.contentWindow.ketcher) {
            sketchers[sketcher_id] = iframe.contentWindow.ketcher;
            clearInterval(checkInterval);
        }
    }, 100);
}

// Detect whether a MOL string is "empty"
// This is a direct copy from chemdraw_utils.js
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

    // V2000: find a line that ends with V2000 and parse first two counts
    var lines = s.split('\n');
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (/\bV2000\b/.test(line)) {
            var trimmed = line.trim();
            var mV2000 = trimmed.match(/^(\d+)\s+(\d+)\b.*\bV2000\b/);
            if (mV2000) {
                var aV2 = parseInt(mV2000[1], 10);
                var bV2 = parseInt(mV2000[2], 10);
                if (!isNaN(aV2) && !isNaN(bV2) && aV2 === 0 && bV2 === 0) return true;
            }
            if (line.length >= 6) {
                var aAlt = parseInt(line.substr(0, 3), 10);
                var bAlt = parseInt(line.substr(3, 3), 10);
                if (!isNaN(aAlt) && !isNaN(bAlt) && aAlt === 0 && bAlt === 0) return true;
            }
        }
    }
    return false;
}

/**
 * Retrieve representation from sketcher
 * @param {string} sketcher_id - ID of the sketcher
 * @param {string} input_element_id - ID of input to update
 * @param {string} format - 'mol' or 'smiles' (defaults to 'mol')
 */
function get_mol_from_sketcher(sketcher_id, input_element_id, format) {
    var sketcher = sketchers[sketcher_id];
    if (!sketcher) {
        // Fallback: check if it's in the iframe but not in dictionary yet
        var iframe = document.getElementById(sketcher_id + "-iframe");
        if (iframe && iframe.contentWindow && iframe.contentWindow.ketcher) {
            sketcher = iframe.contentWindow.ketcher;
            sketchers[sketcher_id] = sketcher;
        } else {
            // Note: we don't log error here because this might be called 
            // before the iframe finishes loading.
            return;
        }
    }
    
    // Resolve the hidden input element
    var input_element = document.getElementById(input_element_id);
    if (!input_element) {
        console.error("Input element not found for: " + input_element_id);
        return;
    }
    
    // Select correct API method based on format
    // Both methods are asynchronous in Ketcher and return a Promise
    var promise = (format === 'smiles') ? sketcher.getSmiles() : sketcher.getMolfile();

    promise.then(function(data) {
        // Check for emptiness based on format
        var isEmpty = (format === 'smiles') ? (!data || !data.trim()) : is_mol_empty(data);
        var newOutStr = isEmpty ? "" : String(data);

        // Determine if current value matches new value
        var oldValStr = input_element.value == null ? "" : String(input_element.value);
        
        // Update the hidden input's value only if it changed
        if (newOutStr !== oldValStr) {
            input_element.value = newOutStr;
            
            // Notify listeners (e.g., HTMX)
            try {
                input_element.dispatchEvent(new Event('input', { bubbles: true }));
                input_element.dispatchEvent(new Event('change', { bubbles: true }));
            } catch (e) {
                // Older browsers fallback
            }
        }
    }).catch(function(error) {
        console.error("Error retrieving " + format.toUpperCase() + ": ", error);
    });
}


// Enable auto-write of molecule data to a hidden input on every sketcher change.
function enable_mol_autowrite(sketcher_id, input_element_id, format, options) {
    options = options || {};
    var debounceMs = typeof options.debounceMs === 'number' ? options.debounceMs : 500; // default to 500ms
    var triggerInitial = options.triggerInitial !== false;

    function wire(sketcher) {
        var timer = null;
        
        // Use the editor API to subscribe to changes
        // API docs: https://github.com/epam/ketcher/blob/master/README.md#ketcher-api
        if (sketcher.editor && typeof sketcher.editor.subscribe === 'function') {
            sketcher.editor.subscribe('change', function (_event) {
                if (timer) {
                    clearTimeout(timer);
                }
                if (debounceMs > 0) {
                    timer = setTimeout(function () {
                        get_mol_from_sketcher(sketcher_id, input_element_id, format);
                    }, debounceMs);
                } else {
                    get_mol_from_sketcher(sketcher_id, input_element_id, format);
                }
            });
        } else {
            console.error("Ketcher editor subscribe method not found.");
        }

        if (triggerInitial) {
            get_mol_from_sketcher(sketcher_id, input_element_id, format);
        }
    }

    var sketcher = sketchers[sketcher_id];
    if (sketcher) {
        wire(sketcher);
        return;
    }

    // If called before the sketcher is attached, retry briefly.
    var tries = 50; 
    var waiter = setInterval(function () {
        var sk = sketchers[sketcher_id];
        if (sk) {
            clearInterval(waiter);
            wire(sk);
        } else if (--tries <= 0) {
            clearInterval(waiter);
            // console.warn("enable_mol_autowrite: waiting for ketcher...");
        }
    }, 200);
}
