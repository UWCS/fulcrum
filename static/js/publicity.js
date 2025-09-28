document.addEventListener("DOMContentLoaded", () => {
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

    // download png button
    const savePngButton = document.getElementById("save-png");
    savePngButton.addEventListener("click", function (event) {
        // get svg element
        const svgElement = document.getElementById("svg-container").querySelector("svg");
        if (!svgElement) {
            alert("No SVG found to convert to PNG.");
            return;
        }

        // serialise svg to string
        const svgData = new XMLSerializer().serializeToString(svgElement);
        const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(svgBlob);

        // create image element to load svg
        const img = new Image();
        img.onload = function () {
            // create canvas to draw image
            const canvas = document.createElement("canvas");
            canvas.width = 2028;
            canvas.height = 2028;

            // draw image to canvas
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

            // convert canvas to blob
            canvas.toBlob(function (blob) {
                // download as png
                // create link element to trigger download
                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = "publicity.png";
                document.body.appendChild(link);

                // clicl link to trigger download
                link.click();

                // remove link element
                document.body.removeChild(link);
                URL.revokeObjectURL(link.href);
            }, "image/png");
            URL.revokeObjectURL(url);
        };
        img.src = url;
    });

    const copyPng = document.getElementById("copy-png");
    copyPng.addEventListener("click", function (event) {
        // get svg element
        const svgElement = document.getElementById("svg-container").querySelector("svg");
        if (!svgElement) {
            alert("No SVG found to convert to PNG.");
            return;
        }
        // serialise svg to string
        const svgData = new XMLSerializer().serializeToString(svgElement);
        const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(svgBlob);
        // create image element to load svg
        const img = new Image();
        img.onload = function () {
            // create canvas to draw image
            const canvas = document.createElement("canvas");
            canvas.width = 2028;
            canvas.height = 2028;
            // draw image to canvas
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            // convert canvas to blob
            canvas.toBlob(function (blob) {
                // copy to clipboard
                const item = new ClipboardItem({ "image/png": blob });
                navigator.clipboard.write([item]).then(() => {
                    // show success state
                    copyPng.classList.remove("btn-outline-secondary");
                    copyPng.classList.add("btn-success");
                    copyPng.innerHTML = "<i class='ph-bold ph-check'></i> Copied";
                    // revert after 2 seconds
                    setTimeout(() => {
                        copyPng.classList.remove("btn-success");
                        copyPng.classList.add("btn-outline-secondary");
                        copyPng.innerHTML = "Copy PNG";
                    }, 2000);
                });
                URL.revokeObjectURL(url);
            }, "image/png");
        };
        img.src = url;
    });
});