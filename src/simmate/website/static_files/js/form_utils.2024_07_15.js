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
