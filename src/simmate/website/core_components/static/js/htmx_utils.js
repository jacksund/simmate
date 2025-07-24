// Allows us to perform an HTML swap AND run JS after
function runJsonActions(actions) {
    actions.forEach(function(action) {
        for (var method in action) {
            if (window[method] && typeof window[method] === "function") {
                window[method](...(action[method] || []));
            }
        }
    });
}

// Allows us to handle a JsonResponse, with no swap involved
document.addEventListener("DOMContentLoaded", function() {
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        var xhr = evt.detail.xhr;
        try {
            var actions = JSON.parse(xhr.responseText);
            actions.forEach(function(action) {
                for (var method in action) {
                    if (window[method] && typeof window[method] === "function") {
                        window[method](...(action[method] || []));
                    }
                }
            });
        } catch (e) {
            // Not JSON, do nothing
        }
    });
});

// Example methods
function showAlert(message) {
    alert(message);
}
function highlight(selector) {
    document.querySelector(selector).style.background = "yellow";
}
