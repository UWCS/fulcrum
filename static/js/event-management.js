// This script validates the form inputs before submission and updates fields if necessary

document.addEventListener("DOMContentLoaded", () => {
    // load icons from the datalist options
    const icons = Array.from(document.querySelectorAll("#icon-list option")).map(option => option.value.trim());

    // load colours from invisible element
    const colours = {};
    const invisibleColours = document.querySelectorAll("#invisible-colours span");
    invisibleColours.forEach(span => {
        const [name, hex] = span.textContent.trim().split(":");
        colours[name] = hex;
    });

    // update icon preview
    const iconInput = document.getElementById("icon");
    const iconPreview = document.getElementById("icon-preview");
    const customIconPreview = document.getElementById("custom-icon-preview");

    iconInput.addEventListener("input", () => {
        if (iconInput.value.startsWith("ph-")) {
            // remove the "ph-" prefix if it exists
            iconInput.value = iconInput.value.substring(3);
        }

        const newClass = "ph-" + iconInput.value.trim();
        iconPreview.className = "ph-bold " + newClass;

        if (window.getComputedStyle(iconPreview, "::before").content !== "none") {
            // if valid phosphor icon, show the icon preview and remove custom icon preview
            customIconPreview.classList.add("d-none");
        } else if (icons.includes(iconInput.value)) {
            // if the icon is one of the predefined icons, show it
            customIconPreview.classList.remove("d-none");
            customIconPreview.maskImage = `url('/static/icons/${iconInput.value}.svg')`;
            customIconPreview.style.maskImage = `url('/static/icons/${iconInput.value}.svg')`;
        } else {
            // show phosphor logo if invalid
            iconPreview.className = "ph-bold ph-phosphor-logo";
            customIconPreview.classList.add("d-none");
        }
    });

    // icon validation
    iconInput.addEventListener("input", () => {
        if (iconInput.value === "" || !iconPreview.className.includes("ph-phosphor-logo") || icons.includes(iconInput.value)) {
            // valid if empty, valid phosphor icon, or one of the predefined icons
            iconInput.setCustomValidity("");
        } else {
            iconInput.setCustomValidity("Please provide a valid Phosphor Icon name or one of: " + icons.join(", "));
        }
    });

    // update colour preview
    const colourPicker = document.getElementById("color_colour");
    const colourText = document.getElementById("text_colour");

    function syncColourInputs(fromText) {
        if (fromText) {
            if (Object.keys(colours).includes(colourText.value)) {
                colourPicker.value = colours[colourText.value]; // set the colour picker to the named colour
            } else if (colourText.value.startsWith("#")) {
                colourPicker.value = colourText.value; // set the colour picker to the text value
            } else {
                colourPicker.value = "#" + colourText.value; // prepend '#' if not present
            }
        } else {
            colourText.value = colourPicker.value.substring(1); // remove the '#' character
        }
    }

    colourPicker.addEventListener("input", () => syncColourInputs(false));
    colourText.addEventListener("input", () => syncColourInputs(true));

    // colour validation
    colourText.addEventListener("input", () => {
        const isHex = /^#?[0-9A-Fa-f]{6}$/;
        if (colourText.value === "" || colourText.value.match(isHex) || Object.keys(colours).includes(colourText.value)) {
            colourText.setCustomValidity("");
        } else {
            colourText.setCustomValidity("Please provide a valid hex color code or one of: " + Object.keys(colours).join(", "));
        }
    });

    // update duration/end time
    const endTimeInput = document.getElementById("end_time");
    const durationInput = document.getElementById("duration");
    const startTimeInput = document.getElementById("start_time");

    function formatDateTimeInput(input) {
        // format the input value to YYYY-MM-DDTHH:MM
        const pad = (num) => num.toString().padStart(2, "0");
        const year = input.getFullYear();
        const month = pad(input.getMonth() + 1); // months are zero-indexed
        const day = pad(input.getDate());
        const hours = pad(input.getHours());
        const minutes = pad(input.getMinutes());
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    function updateDuration() {
        if (startTimeInput.value && endTimeInput.value) {
            const startTime = new Date(startTimeInput.value);
            const endTime = new Date(endTimeInput.value);

            let duration = endTime - startTime;
            if (duration < 0) {
                duration = 0;
            }
            // convert duration into DD:HH:MM format
            const days = Math.floor(duration / (1000 * 60 * 60 * 24));
            const hours = Math.floor((duration % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));

            // prepend 0s if necessary
            const formattedDuration = [
                days.toString().padStart(2, '0'),
                hours.toString().padStart(2, '0'),
                minutes.toString().padStart(2, '0')
            ].join(':');
            durationInput.value = formattedDuration;
        }
    }

    function updateEndTime() {
        if (startTimeInput.value && durationInput.value) {
            // confirm that the duration is in DD:HH:MM format
            if (/^\d{2}:(?:[01]\d|2[0-3]):[0-5]\d$/.test(durationInput.value)) {
                const [days, hours, minutes] = durationInput.value.split(':').map(Number);
                const startTime = new Date(startTimeInput.value);

                // calculate end time
                startTime.setDate(startTime.getDate() + days);
                startTime.setHours(startTime.getHours() + hours);
                startTime.setMinutes(startTime.getMinutes() + minutes);

                // update end time input
                endTimeInput.value = formatDateTimeInput(startTime);
            }
        }
    }

    startTimeInput.addEventListener("input", () => {
        updateDuration();
        updateEndTime();
    });
    durationInput.addEventListener("input", () => updateEndTime());
    endTimeInput.addEventListener("input", () => updateDuration());

    // check if end time is after start time
    endTimeInput.addEventListener("input", () => {
        if (startTimeInput.value && endTimeInput.value) {
            const startTime = new Date(startTimeInput.value);
            const endTime = new Date(endTimeInput.value);

            if (endTime <= startTime) {
                endTimeInput.setCustomValidity("End time must be after start time");
            } else {
                endTimeInput.setCustomValidity("");
            }
        }
    });

    // check if endtime = starttime + duration
    endTimeInput.addEventListener("input", () => {
        if (startTimeInput.value && durationInput.value) {
            const startTime = new Date(startTimeInput.value);
            const [days, hours, minutes] = durationInput.value.split(':').map(Number);
            startTime.setDate(startTime.getDate() + days);
            startTime.setHours(startTime.getHours() + hours);
            startTime.setMinutes(startTime.getMinutes() + minutes);
            const endTime = new Date(endTimeInput.value);
            if (endTime.getTime() !== startTime.getTime()) {
                endTimeInput.setCustomValidity("End time does not match duration");
            } else {
                endTimeInput.setCustomValidity("");
            }
        }
    });


    // form validation
    const form = document.querySelector("form");
    form.addEventListener("submit", (event) => {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add("was-validated");

        // prepend "#" to text colour
        if (colourText.value && !colourText.value.startsWith("#") && !Object.keys(colours).includes(colourText.value)) {
            colourText.value = "#" + colourText.value;
        }
    }, false);

    // trigger events on load
    [iconInput, colourText, startTimeInput, endTimeInput].forEach(input => {
        if (input && input.value) {
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
});