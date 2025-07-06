// This script validates the form inputs before submission and updates fields if necessary

document.addEventListener("DOMContentLoaded", () => {

    // MARK: icons

    // update icon preview
    const iconInput = document.getElementById("icon");
    const iconPreview = document.getElementById("icon-preview");
    const customIconPreview = document.getElementById("custom-icon-preview");

    // load icons from the datalist options
    const icons = Array.from(document.querySelectorAll("#icon-list option")).map(option => option.value.trim());

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

    // MARK: colours

    // update colour preview
    const colourPicker = document.getElementById("color_colour");
    const colourText = document.getElementById("text_colour");

    // load colours from invisible element
    const colours = {};
    const invisibleColours = document.querySelectorAll("#invisible-colours span");
    invisibleColours.forEach(span => {
        const [name, hex] = span.textContent.trim().split(":");
        colours[name] = hex;
    });

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

    // MARK: time entry

    const timeFields = document.getElementById("time-fields");
    const addTimeButton = document.getElementById("add-time");
    const durationInput = document.getElementById("duration");

    let eventDuration = 0; // duration in ms

    function formatDateTimeInput(input) {
        // format the input value to YYYY-MM-DDTHH:MM
        if (!(input instanceof Date)) return "";
        const pad = (num) => num.toString().padStart(2, "0");
        const year = input.getFullYear();
        const month = pad(input.getMonth() + 1); // months are zero-indexed
        const day = pad(input.getDate());
        const hours = pad(input.getHours());
        const minutes = pad(input.getMinutes());
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    function formatDuration(input) {
        // convert ms into DD:HH:MM format
        if (input < 0) input = 0;
        const days = Math.floor(input / (1000 * 60 * 60 * 24));
        const hours = Math.floor((input % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((input % (1000 * 60 * 60)) / (1000 * 60));
        return [
            days.toString().padStart(2, "0"),
            hours.toString().padStart(2, "0"),
            minutes.toString().padStart(2, "0")
        ].join(":");
    }

    function parseDuration(input) {
        // parse DD:HH:MM format into milliseconds
        if (!/^\d{2}:\d{2}:\d{2}$/.test(input)) return 0;
        const [days, hours, minutes] = input.split(":").map(Number);
        return (days * 24 * 60 * 60 + hours * 60 * 60 + minutes * 60) * 1000;
    }

    function validateEndTime(endTimeInput) {
        // makes sure the end time is after the start time
        const entry = endTimeInput.closest(".time-entry");
        const startTimeInput = entry.querySelector("input[name='start_time[]']");
        if (!startTimeInput || !endTimeInput) return;
        const startTime = new Date(startTimeInput.value);
        const endTime = new Date(endTimeInput.value);
        if (startTime >= endTime) {
            endTimeInput.setCustomValidity("End time must be after start time.");
        } else {
            endTimeInput.setCustomValidity("");
        }
    }

    function syncEndTimes() {
        // sync all end times based on the start time and event duration
        document.querySelectorAll(".time-entry").forEach(entry => {
            const startTimeInput = entry.querySelector("input[name='start_time[]']");
            const endTimeInput = entry.querySelector("input[name='end_time[]']");
            if (!startTimeInput) return;
            const startTime = new Date(startTimeInput.value);
            const endTime = new Date(startTime.getTime() + eventDuration);
            endTimeInput.value = formatDateTimeInput(endTime);
            validateEndTime(endTimeInput);
        });
    }

    function updateDuration(endInput) {
        // update duration 
        const entry = endInput.closest(".time-entry");
        if (!entry) return;

        const startTimeInput = entry.querySelector("input[name='start_time[]']");

        if (!startTimeInput || !startTimeInput.value || !endInput.value) return;

        const startTime = new Date(startTimeInput.value);
        const endTime = new Date(endInput.value);
        const duration = endTime.getTime() - startTime.getTime();

        if (duration < 0) {
            // invalid duration
            endInput.setCustomValidity("End time must be after start time.");
            return;
        }

        // update the duration input
        endInput.setCustomValidity("");
        eventDuration = duration;
        durationInput.value = formatDuration(eventDuration);

        // sync accross all end times
        syncEndTimes();
    }

    function updateFutureStartTimes(changedInput) {
        // update all future start times based on the changed input
        const allEntries = Array.from(timeFields.querySelectorAll(".time-entry"));
        const currentIndex = allEntries.findIndex(entry => entry.contains(changedInput));

        if (currentIndex < 0 || currentIndex + 1 >= allEntries.length) return;

        let delta = 7 * 24 * 60 * 60 * 1000; // default is a week
        if (currentIndex > 0) {
            // if multiple entries, set the delta to the duration of the previous entry
            const previousEntry = allEntries[currentIndex - 1].querySelector("input[name='start_time[]']");
            if (previousEntry.value && changedInput.value) {
                delta = new Date(changedInput.value).getTime() - new Date(previousEntry.value).getTime();
            }
        }

        for (let i = currentIndex + 1; i < allEntries.length; i++) {
            // update the start time of the next entries
            const prevStartInput = allEntries[i - 1].querySelector("input[name='start_time[]']");
            const currStartInput = allEntries[i].querySelector("input[name='start_time[]']");
            const currEndInput = allEntries[i].querySelector("input[name='end_time[]']");

            if (!prevStartInput.value) continue;

            const newStartTime = new Date(new Date(prevStartInput.value).getTime() + delta);
            currStartInput.value = formatDateTimeInput(newStartTime);
            const newEndTime = new Date(newStartTime.getTime() + eventDuration);
            currEndInput.value = formatDateTimeInput(newEndTime);
            validateEndTime(currEndInput);
        }
    }

    function toggleAddTimeButton() {
        // enable or disable the add time button if the first entry has a start time
        const firstTimeInput = timeFields.querySelector("input[name='start_time[]']");
        if (firstTimeInput && firstTimeInput.value) {
            addTimeButton.classList.remove("disabled");
        } else {
            addTimeButton.classList.add("disabled");
        }
    }

    timeFields.addEventListener("input", (event) => {
        // handle input changes in time fields
        const input = event.target;

        toggleAddTimeButton();

        if (input.name === "start_time[]") {
            // if start time changes, update future start times and end times
            document.getElementById("add-time").classList.remove("disabled");
            updateFutureStartTimes(input);
            const entry = input.closest(".time-entry");
            const endTimeInput = entry.querySelector("input[name='end_time[]']");
            const startTime = new Date(input.value);
            if (eventDuration <= 0) return; // if no valid duration, do not update end time
            endTimeInput.value = formatDateTimeInput(new Date(startTime.getTime() + eventDuration));
            validateEndTime(endTimeInput);
        } else if (input.name === "end_time[]") {
            // if end time changes, update duration and validate end time
            updateDuration(input);
            validateEndTime(input);
        }
    });

    durationInput.addEventListener("input", () => {
        // handle duration input changes
        duration = parseDuration(durationInput.value);
        if (duration > 0) {
            // if valid duration, update the event duration and sync end times
            eventDuration = duration;
            syncEndTimes();
            durationInput.setCustomValidity("");
        } else {
            // invalid
            durationInput.setCustomValidity("Please provide a valid duration in DD:HH:MM format.");
        }
    });

    if (addTimeButton) {
        addTimeButton.addEventListener("click", (event) => {
            // add a new time entry
            const allEntries = timeFields.querySelectorAll(".time-entry");

            const lastEntry = allEntries[allEntries.length - 1];
            const prevStartInput = lastEntry.querySelector("input[name='start_time[]']");
            if (!prevStartInput || !prevStartInput.value) return;

            let delta = 7 * 24 * 60 * 60 * 1000; // default is a week
            if (allEntries.length > 1) {
                // if multiple entries, set the delta to the duration of the previous entry
                const penultimateEntry = allEntries[allEntries.length - 2];
                const penultimateStartInput = penultimateEntry.querySelector("input[name='start_time[]']");
                delta = new Date(prevStartInput.value).getTime() - new Date(penultimateStartInput.value).getTime();
            }

            const newStartTime = new Date(new Date(prevStartInput.value).getTime() + delta);
            const newEndTime = eventDuration > 0 ? new Date(newStartTime.getTime() + eventDuration) : NaN;

            // create a new time entry element and add
            const newEntry = document.createElement("div");
            newEntry.className = "row g-3 mt-0 time-entry";
            newEntry.innerHTML = `
                <div class="form-floating col-md-4">
                    <input type="datetime-local" name="start_time[]" id="start_time" class="form-control" value="${formatDateTimeInput(newStartTime)}" required>
                    <label for="start_time">Start Time</label>
                    <div class="invalid-feedback">Please provide a start time</div>
                    <div class="valid-feedback">Looks good!</div>
                </div>

                <div class="form-floating col-md-4">
                    <input type="datetime-local" name="end_time[]" id="end_time" class="form-control" value="${formatDateTimeInput(newEndTime)}">
                    <label for="end_time">End Time</label>
                    <div class="invalid-feedback">Endtime must be after start time and match the duration</div>
                    <div class="valid-feedback">Looks good!</div>
                </div>

                <div class="col-md-4 d-flex align-items-center">
                    <button type="button" class="btn btn-danger d-flex align-items-center gap-1 remove-time-entry">
                        <i class="ph-bold ph-trash"></i> Remove
                    </button>
                </div>
            `;
            timeFields.appendChild(newEntry);
        });
    }

    timeFields.addEventListener("click", (event) => {
        // remove a time entry
        if (!event.target.classList.contains("remove-time-entry")) return;
        const entry = event.target.closest(".time-entry").remove();
    });

    function initialiseTimes() {
        // initialise the time fields with the first entry's values

        const firstEntry = timeFields.querySelector(".time-entry");
        if (!firstEntry) return;

        const startTimeInput = firstEntry.querySelector("input[name='start_time[]']");
        const endTimeInput = firstEntry.querySelector("input[name='end_time[]']");

        if (startTimeInput.value && endTimeInput.value) {
            // if start and end times are set, calculate the duration
            const initialDuration = new Date(endTimeInput.value).getTime() - new Date(startTimeInput.value).getTime();
            if (initialDuration >= 0) {
                eventDuration = initialDuration;
                durationInput.value = formatDuration(eventDuration);
            }
        } else {
            // otherwise attempt to use the duration input
            const initialDuration = parseDuration(durationInput.value);
            if (initialDuration > 0) {
                eventDuration = initialDuration;
                if (startTimeInput.value) {
                    const startTime = new Date(startTimeInput.value);
                    endTimeInput.value = formatDateTimeInput(new Date(startTime.getTime() + eventDuration));
                }
            }
        }

        // validate end times
        document.querySelectorAll("input[name='end_time[]']").forEach(validateEndTime);

        toggleAddTimeButton();
    }

    initialiseTimes();

    // MARK: form validation

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
    [iconInput, colourText].forEach(input => {
        if (input && input.value) {
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
});