var chemdrawjs_failed = function (error) {
    alert(error);
};

var add_mol_sketcher = function (sketcher_id) {
    perkinelmer.ChemdrawWebManager.attach({
        id: sketcher_id,
        errorCallback: chemdrawjs_failed,
        licenseUrl: ChemDrawLicenseURL, // global var set in site_base.html
    });
};

var get_mol_from_sketcher = function (
    sketcher,
    textarea_id,
    unicorn_view,
    unicorn_method,
) {
    console.log("HERE")
};
// NOTE: this code is how you'd pre-populate a sketcher. I hold on to
// this for future reference.
// perkinelmer.ChemdrawWebManager.attach({
//     id: 'chemdrawjs-container2',
//     callback: chemdrawjsAttached,
//     errorCallback: chemdrawjsFailed,
//     licenseUrl: '{% static "/licenses/ChemDraw-JS-License.xml" %}'
// });
// var chemdrawjsAttached = function (chemdraw) {
//     chemdraw.loadSMILES('C1=CC=CC=C1', function (result, error) {
//         if (error) {
//             alert(error);
//         }
//         });
// };