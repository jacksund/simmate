// for grabbing a form's inputs to be used as JSON elsewhere
function getFormValues(form_id) {
    const form = document.getElementById(form_id);
    const formData = new FormData(form);
    const values = {};
    formData.forEach((value, key) => {
        values[key] = value;
    });
    // django-unicorn needs these as json
    return JSON.stringify(values);
}
// for toggling via a "select-all" button
// Code from: https://stackoverflow.com/questions/386281/
function toggle_select_all(source, target_class) {
    // assumes all child elements have the same name
    checkboxes = document.getElementsByClassName(target_class);
    for(var i=0, n=checkboxes.length;i<n;i++) {
        checkboxes[i].checked = source.checked;
    }
}
// for allowing AJAX-based file uploads
// code from: https://github.com/adamghill/django-unicorn/discussions/256#discussioncomment-7937302 #}
function add_file_upload_listener(containerId, maxSizeMB) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id "${containerId}" not found.`);
        return;
    }

    const fileInput = container.querySelector('input[type="file"]');
    const hiddenInput = container.querySelector('input.file-data');

    if (!fileInput || !hiddenInput) {
        console.error('File input or hidden input not found in container:', containerId);
        return;
    }

    fileInput.addEventListener('input', function (e) {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const fileSizeMB = file.size / (1024 * 1024);

            if (fileSizeMB > maxSizeMB) {
                alert(`File size exceeds the limit of ${maxSizeMB}MB.`);
                fileInput.value = ""; // reset the input
                hiddenInput.value = "";
                return;
            }

            const reader = new FileReader();
            reader.onload = function (event) {
                hiddenInput.value = event.target.result;
                // "bubble up" through the DOM tree (i.e., trigger a refresh in dj-unicorn)
                hiddenInput.dispatchEvent(new Event('input', {bubbles: true}));
            };
            reader.readAsDataURL(file);
        } else {
            alert('Please select a file');
        }
    });
}
