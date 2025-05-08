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
