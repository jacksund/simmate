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


document.addEventListener("DOMContentLoaded", function() {
    // Allows us to handle a JsonResponse, with no swap involved
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
    // Automatically attaches the body's csrf token to htmx posts
    document.body.addEventListener("htmx:configRequest", (event) => {
      const token = document.querySelector("[name=csrfmiddlewaretoken]").value;
      event.detail.headers["X-CSRFToken"] = token;
    });
});


// Example methods
function showAlert(message) {
    alert(message);
}
function highlight(selector) {
    document.querySelector(selector).style.background = "yellow";
}
