document.addEventListener("DOMContentLoaded", () => {
    // load base elements
    const searchInput = document.getElementById("search-input");
    const searchSuggestions = document.getElementById("search-suggestions");
    const searchForm = document.getElementById("search-form");

    // initalise variables
    let suggestions = [];
    let highlightedIndex = -1;
    const SUGGESTION_LIMIT = 5;
    let currentAbortController = null; // for aborting fetch requests

    function showSuggestions() {
        // show or hide the suggestions dropdown
        if (suggestions.length) {
            searchSuggestions.classList.add("show");
            searchInput.setAttribute("aria-expanded", "true");
        } else {
            searchSuggestions.classList.remove("show");
            searchInput.setAttribute("aria-expanded", "false");
        }
    }

    function clearSuggestions() {
        // clear suggestions and reset state
        suggestions = [];
        highlightedIndex = -1;
        searchSuggestions.innerHTML = "";
        showSuggestions();
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
            a.setAttribute("role", "option");

            a.addEventListener("click", (event) => {
                // if clicked, prevent following hyperlink and search for the suggestion
                event.preventDefault();
                chooseSuggestion(index);
                searchForm.submit();
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

    function chooseSuggestion(item) {
        // set the search input to the chosen suggestion and clear suggestions
        if (item < 0 || item >= suggestions.length) return;
        searchInput.value = suggestions[item];
        clearSuggestions();
        searchInput.focus();
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
        const url = `/api/search/complete/?${params.toString()}`;

        fetch(url, { signal }) // fetch suggestions and render
            .then(response => response.ok ? response.json() : [])
            .then(data => Array.isArray(data) ? renderSuggestions(data) : [])
            .catch(error => {
                if (error.name === "AbortError") return;
                console.error("Error fetching suggestions:", error);
                clearSuggestions();
            })
    }

    function onInput() {
        const query = searchInput.value.trim();

        if (query.length < 3) { // only suggest after 3 chars, as we can only now suggest anything meaningful
            clearSuggestions();
            return;
        }

        fetchSuggestions(query);
    }

    function onKeyDown(event) {
        if (!suggestions.length) return;

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
                    chooseSuggestion(highlightedIndex);
                    searchForm.submit();
                }
                break;
            case "Tab": // tab fills in the highlighted suggestion (but does not submit the form)
                if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
                    event.preventDefault();
                    chooseSuggestion(highlightedIndex);
                }
                break;
            case "Escape": // hide suggestions
                clearSuggestions();
                break;
        }
    }

    // add listeners
    searchInput.addEventListener("input", onInput);
    searchInput.addEventListener("keydown", onKeyDown);

    // if blur, clear suggestions after a short delay to allow click events to register
    searchInput.addEventListener("blur", () => setTimeout(clearSuggestions, 100));

    // clear if clicked outside the search form or suggestions
    document.addEventListener("click", (event) => {
        if (!searchForm.contains(event.target) && !searchSuggestions.contains(event.target)) {
            clearSuggestions();
        }
    });
});