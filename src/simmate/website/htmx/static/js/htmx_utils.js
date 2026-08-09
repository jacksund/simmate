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
    document.body.addEventListener('htmx:afterRequest', function(evt) {
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
    
    // Handle HTMX Response Errors (like 500 when component cache fails)
    document.body.addEventListener('htmx:responseError', function(evt) {
        const xhr = evt.detail.xhr;
        let errorMsg = "An unexpected error occurred. Please try again.";
        if (xhr.status >= 500) {
            errorMsg = `Server Error (${xhr.status}). If the server recently updated or restarted, you may need to refresh the page.
            <div class="mt-2 pt-2 border-top border-light">
                <button type="button" class="btn btn-sm btn-light" onclick="window.location.reload()">Refresh Page</button>
            </div>`;
        }
        // Use a fixed ID so we don't spam the user with toasts if an element is polling
        showToast(errorMsg, "Backend Error", "danger", "htmx-response-error-toast");
    });

    // Handle HTMX Send Errors (when the backend is down or network is disconnected)
    document.body.addEventListener('htmx:sendError', function(evt) {
        const errorMsg = `Unable to reach the server. The server might be down or you may have lost your connection.
        <div class="mt-2 pt-2 border-top border-light">
            <button type="button" class="btn btn-sm btn-light" onclick="window.location.reload()">Refresh Page</button>
        </div>`;
        showToast(errorMsg, "Network Error", "warning", "htmx-send-error-toast");
    });
});


// Example methods
function showAlert(message) {
    alert(message);
}
function highlight(selector) {
    document.querySelector(selector).style.background = "yellow";
}
function extendPlotlyTrace(componentId, xData, yData, maxPoints=10000) {
    var graphDiv = document.getElementById(componentId);
    if (graphDiv) {
        // Plotly.extendTraces(graphDiv, update, traceIndices, maxPoints)
        Plotly.extendTraces(graphDiv, {x: [xData], y: [yData]}, [0], maxPoints);
    } else {
        console.warn("Graph div not found for componentId: " + componentId);
    }
}

function showToast(message, title="Error", variant="danger", toastId="dynamic-toast") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container position-fixed bottom-0 start-0 p-3";
        container.style.zIndex = "1100";
        document.body.appendChild(container);
    }
    
    // Check if this specific toast already exists to prevent spamming
    let existingToast = document.getElementById(toastId);
    if (existingToast) {
        const toast = bootstrap.Toast.getInstance(existingToast) || new bootstrap.Toast(existingToast);
        toast.show();
        return;
    }

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${variant} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="15000">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br/>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML("beforeend", toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}
