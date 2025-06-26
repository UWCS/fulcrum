// This script validates the form inputs before submission and updates fields if necessary

document.addEventListener("DOMContentLoaded", function () {
    // update icon preview
    // TODO: add custom uploads for icons
    const iconInput = document.getElementById("icon");
    const iconPreview = document.getElementById("icon-preview");

    iconInput.addEventListener("input", function () {
        if (iconInput.value.startsWith("ph-")) {
            // remove the "ph-" prefix if it exists
            iconInput.value = iconInput.value.substring(3);
        }

        const newClass = "ph-" + iconInput.value.trim();
        iconPreview.className = "ph-bold " + newClass;

        // check if the icon is valid
        isValid = window.getComputedStyle(iconPreview, "::before").content !== "none";
        if (!isValid) {
            // default to generic icon if invalid
            iconPreview.className = "ph-bold ph-phosphor-logo"
        }
    });

    // update colour preview
    const colourPicker = document.getElementById("color_colour");
    const colourText = document.getElementById("text_colour");

    function syncColourInputs(fromText) {
        if (fromText) {
            colourPicker.value = "#" + colourText.value;
        }
        else {
            colourText.value = colourPicker.value.substring(1); // remove the '#' character
        }
    }

    colourPicker.addEventListener("input", () => syncColourInputs(false));
    colourText.addEventListener("input", () => syncColourInputs(true));

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
            console.log(`Duration: ${formattedDuration}`);
            durationInput.value = formattedDuration;
        }
    }

    function updateEndTime() {
        if (startTimeInput.value && durationInput.value) {
            // confirm that the duration is in DD:HH:MM format
            if (/^\d{1,2}:(?:[01]\d|2[0-3]):[0-5]\d$/.test(durationInput.value)) {
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
});