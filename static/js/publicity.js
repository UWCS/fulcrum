document.addEventListener("DOMContentLoaded", () => {
    // submit form with svg content as file
    const form = document.getElementById("publicity-form");
    form.addEventListener("submit", function (event) {
        const svgContent = document.getElementById("svg-container").innerHTML;
        const blob = new Blob([svgContent], { type: "image/svg+xml" });
        const fileInput = document.getElementById("svg");
        const file = new File([blob], "publicity.svg", { type: "image/svg+xml" });

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
    });

    // enforce week range (set options for endweek based on startweek)
    const startWeekInput = document.getElementById("start-week");
    const endWeekInput = document.getElementById("end-week");
    const endWeekSelected = endWeekInput.getAttribute("data-selected");
    startWeekInput.addEventListener("input", function () {
        const startWeek = parseInt(this.value);
        if (!isNaN(startWeek)) {
            // set end week options and select value if it matches
            endWeekInput.innerHTML = `
                <option value="" disabled>Select a start week to enable</option>
                <option value="${startWeek}" ${endWeekSelected == startWeek ? "selected" : ""}>${startWeek}</option>
                <option value="${startWeek + 5}" ${endWeekSelected == startWeek + 5 ? "selected" : ""}>${startWeek + 5}</option>
            `;
        } else {
            endWeekInput.innerHTML = `<option value="" disabled selected>Select a start week to enable</option>`;
        }
    });
    if (startWeekInput.value) {
        startWeekInput.dispatchEvent(new Event("input"));
    }

    // copy svg button
    const copyButton = document.getElementById("copy-svg");
    copyButton.addEventListener("click", function (event) {
        event.preventDefault(); // stop form submission
        const svgContent = document.getElementById("svg-container").innerHTML;
        // copy to clipboard
        navigator.clipboard.writeText(svgContent).then(() => {
            // show success state
            copyButton.classList.remove("btn-outline-primary");
            copyButton.classList.add("btn-success");
            copyButton.innerHTML = "<i class='ph-bold ph-check'></i> Copied";

            // revert after 2 seconds
            setTimeout(() => {
                copyButton.classList.remove("btn-success");
                copyButton.classList.add("btn-outline-primary");
                copyButton.innerHTML = "Copy SVG";
            }, 2000);
        });
    });
});