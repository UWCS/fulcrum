document.addEventListener("DOMContentLoaded", function () {
    // initialise filter functions
    const ownerInput = document.getElementById("ownerSearch");
    const activeSelect = document.getElementById("activeFilter");
    const rows = document.querySelectorAll("table tbody tr");

    function filterTable() {
        // get desired filter values
        const ownerValue = ownerInput.value.toLowerCase();
        const activeValue = activeSelect.value;

        rows.forEach(row => {
            // get row values
            const ownerCell = row.children[1]?.textContent.toLowerCase();
            const activeCell = row.children[4]?.textContent.toLowerCase();

            // check if row matches filters
            const matchesOwner = ownerCell.includes(ownerValue);
            const matchesActive = !activeValue || (activeValue === "yes" && activeCell.includes("yes")) || (activeValue === "no" && activeCell.includes("no"));

            // set row visibility based on filters
            if (matchesOwner && matchesActive) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    }

    ownerInput.addEventListener("input", filterTable);
    activeSelect.addEventListener("change", filterTable);
});

function clearFilters() {
    // clear filters and reset table visibility
    document.getElementById("ownerSearch").value = "";
    document.getElementById("activeFilter").value = "";
    const rows = document.querySelectorAll("table tbody tr");
    rows.forEach(row => row.style.display = "");
}