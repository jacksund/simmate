function refresh_select2() {
    // call this after an ajax request to init new select2 inputs
    $('.select2').select2();;
}
function add_dynamic_select2() {
    // call this to allow dynamic input options
    $(".select2-dynamic").select2({tags: true});
}
