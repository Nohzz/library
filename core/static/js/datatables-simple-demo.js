window.addEventListener('DOMContentLoaded', event => {
    // Simple-DataTables
    // https://github.com/fiduswriter/Simple-DataTables/wiki

    const datatablesSimple = document.getElementById('datatablesSimple');
    if (datatablesSimple) {
        new simpleDatatables.DataTable(datatablesSimple, {"perPage": 25});
    }
    const itemstable = document.getElementById('itemstable');
    if (itemstable) {
        new simpleDatatables.DataTable(itemstable, {"perPage": 25});
    }

});
