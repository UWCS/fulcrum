document.addEventListener("DOMContentLoaded", () => {
    // load base elements
    const searchInput = Array.from(document.querySelectorAll("input[name='query']"));
    const searchSuggestions = document.getElementById("search-suggestions");

    // initalise variables
    let suggestions = [];
    let highlightedIndex = -1;
    const SUGGESTION_LIMIT = 5;
    let currentAbortController = null; // for aborting fetch requests
    let activeInput = null; // which of the search bars is currently in use

    function showSuggestions() {
        // show or hide the suggestions dropdown
        if (suggestions.length) {
            searchSuggestions.classList.add("show");
            if (activeInput) activeInput.setAttribute("aria-expanded", "true")
        } else {
            searchSuggestions.classList.remove("show");
            if (activeInput) activeInput.setAttribute("aria-expanded", "false")
        }
    }

    function clearSuggestions() {
        // clear suggestions and reset state
        suggestions = [];
        highlightedIndex = -1;
        searchSuggestions.innerHTML = "";
        showSuggestions();
    }

    function moveDropdownToInput(input) {
        // move the suggestions dropdown to the specified input element
        const group = input.closest(".input-group") || input.parentElement;
        if (group && group !== searchSuggestions.parentElement) {
            group.appendChild(searchSuggestions);
        }
        searchSuggestions.setAttribute("role", "listbox");
        input.setAttribute("aria-haspopup", "listbox");
    }

    function renderSuggestions(items) {
        suggestions = items || [];
        searchSuggestions.innerHTML = "";

        if (!suggestions.length) {
            // remove suggestions if empty
            showSuggestions();
            return;
        }

        suggestions.forEach((item, index) => {
            // create suggestion item
            const a = document.createElement("a");
            a.className = "dropdown-item";
            a.href = `#`;
            a.textContent = item;
            a.title = item; // show on hover
            a.setAttribute("role", "option");

            a.addEventListener("click", (event) => {
                // if clicked, prevent following hyperlink and search for the suggestion
                event.preventDefault();
                chooseSuggestion(index, activeInput);
                if (activeInput && activeInput.form) activeInput.form.submit();
            });

            searchSuggestions.appendChild(a);
        });

        highlightedIndex = -1; // reset highlighted index as new suggestions are rendered
        showSuggestions();
    }

    function setHighlight(index) {
        // highlight the indexth suggestion
        const children = searchSuggestions.querySelectorAll(".dropdown-item");
        children.forEach((child, i) => {
            child.classList.toggle("active", i === index);
        });
        highlightedIndex = index;
    }

    function chooseSuggestion(index, input) {
        // set the search input to the chosen suggestion and clear suggestions
        if (!input || index < 0 || index >= suggestions.length) return;
        input.value = suggestions[index];
        clearSuggestions();
        input.focus();
    }

    function fetchSuggestions(query) {
        // abort any ongoing fetch request
        if (currentAbortController) currentAbortController.abort();
        currentAbortController = new AbortController();
        const signal = currentAbortController.signal;

        // prepare API request
        const params = new URLSearchParams({
            query: query,
            limit: SUGGESTION_LIMIT
        });
        const url = `/api/search/suggestions/?${params.toString()}`;

        fetch(url, { signal }) // fetch suggestions and render
            .then(response => response.ok ? response.json() : [])
            .then(data => Array.isArray(data) ? renderSuggestions(data) : [])
            .catch(error => {
                if (error.name === "AbortError") return;
                console.error("Error fetching suggestions:", error);
                clearSuggestions();
            })
    }

    function onInput(event) {
        const input = event.currentTarget;
        activeInput = input; // set the currently active input
        moveDropdownToInput(input); // ensure dropdown is under the correct input

        const query = input.value.trim();

        if (query.length < 3) { // only suggest after 3 chars, as we can only now suggest anything meaningful
            clearSuggestions();
            return;
        }

        fetchSuggestions(query);
    }

    function onKeyDown(event) {
        const input = event.currentTarget;
        if (input !== activeInput || !suggestions.length) return;

        switch (event.key) {
            case "ArrowDown": // move down the suggestions
                event.preventDefault();
                setHighlight(Math.min(highlightedIndex + 1, suggestions.length - 1));
                break;
            case "ArrowUp": // move up the suggestions
                event.preventDefault();
                setHighlight(Math.max(highlightedIndex - 1, -1));
                break;
            case "Enter": // select the highlighted suggestion and search for it
                if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
                    event.preventDefault();
                    chooseSuggestion(highlightedIndex, activeInput);
                    if (activeInput && activeInput.form) activeInput.form.submit();
                }
                break;
            case "Tab": // tab fills in the highlighted suggestion (but does not submit the form)
                if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
                    event.preventDefault();
                    chooseSuggestion(highlightedIndex, activeInput);
                }
                break;
            case "Escape": // hide suggestions
                clearSuggestions();
                break;
        }
    }

    searchInput.forEach((input) => {
        input.setAttribute("role", "combobox");
        input.setAttribute("aria-autocomplete", "list");
        input.setAttribute("aria-expanded", "false");

        input.addEventListener("input", onInput);
        input.addEventListener("keydown", onKeyDown);

        input.addEventListener("focus", () => {
            activeInput = input;
            moveDropdownToInput(input);
        });

        input.addEventListener("blur", () => setTimeout(() => {
            const active = document.activeElement;
            if (searchSuggestions.contains(active)) return;
            clearSuggestions();
            if (input) input.setAttribute("aria-expanded", "false");
        }, 100))
    });

    document.addEventListener("click", (event) => {
        const clickedInside = searchInput.some(input => input.contains(event.target)) ||
            searchInput.some(input => input === event.target) ||
            searchSuggestions.contains(event.target);
        if (!clickedInside) clearSuggestions();
    });
});