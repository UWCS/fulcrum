<!-- omit from toc -->
# Developer documentation for fulcrum

This documentation is intended for developers working on fulcrum. This explains how to set up fulcrum locally, why some design decisions were made, and anything else you should need. If you need any help, message in #tech-team on the UWCS discord.

If you're a user pls see the [user documentation](USER.md) instead.

<!-- omit from toc -->
## Table of Contents

- [Running](#running)
  - [SSL Note](#ssl-note)
  - [Timezones Note](#timezones-note)
- [Stack](#stack)
- [File Structure](#file-structure)
- [Database schema](#database-schema)
- [API](#api)
  - [Creating and managing API keys](#creating-and-managing-api-keys)
- [Styling](#styling)
- [Icons](#icons)
  - [Updating phosphor icons](#updating-phosphor-icons)
  - [Adding custom icons](#adding-custom-icons)
- [Colours](#colours)
- [Warwick APIs](#warwick-apis)
  - [Warwick Weeks](#warwick-weeks)
  - [Warwick Map API](#warwick-map-api)
- [Testing](#testing)
- [Ideas for the future](#ideas-for-the-future)

## Running

(note on some systems you may need to use `python -m pipenv` instead of `pipenv`)

1. Clone the repo: `git clone https://github.com/uwcs/fulcrum`
2. Install pipenv if you don't have it already: `pip install pipenv`
3. Install dependencies: `pipenv install`
5. Create a `.env` file in the root directory and add the following environment variables:
   ```env
    SECRET_KEY="secret" # for session management, can be anything
    KEYCLOAK_CLIENT_SECRET="secret" # can be found at https://auth.uwcs.co.uk/admin/master/console/#/uwcs/clients/311b91f8-55ba-4847-8c0f-8d9d8ae00c23/credentials
    API_KEY="key" # can be anything, used for testing the apiS
    ```
6. Build the css file: `pipenv run python ./scripts/build_scss.py`
7. (Optional) Add stuff to db
    - Initialise the database: `pipenv run python -m scripts.reset_db`
    - Seeded data can be added by running `pipenv run python -m scripts.reset_db seed`
    - Original data from stardust can be imported by running `pipenv run python -m scripts.import` (this is not officially supported)
8. Run the app: `pipenv run flask --app fulcrum run --debug`

For production, use a gunicorn server:

```bash
pipenv run gunicorn fulcrum:app -b 0.0.0.0:5000
```

Alternarively, you can run the site in a docker container:

```bash
docker build -t fulcrum .
docker run -p 5000:5000 fulcrum
```

### SSL Note

The app uses UWCS's keycloak server for authentication. This is set to enable both http and https as redirect URIs ONLY WHEN RUNNING LOCALLY (127.0.0.1). The app is configured such that if `app.debug` is true, http is used, otherwise https is used. As a result when running locally out of debug mode, https must be used. This can be done by running `pipenv run flask --app fulcrum run --cert=adhoc`.

If you are not exec, you can bypass auth by setting the environment variable `DEV` to `1`.

### Timezones Note

The database currently stores and interprets all datetimes as naive Europe/London dts. An ORM reconstructor is used in the `Event` model to make localising of read dts consistent with what (mostly) previously occurred with a newly constructed `Event`. The API now returns full ISO-8601 dt strings for external usage.

Using `replace` on `tzinfo` with pytz causes inconsistent behaviour, notably causing weird offsets of 1 minute, hence the use of `localize` instead. This is due to LMT shenanigans (see Raven's braindump about this if you're interested: https://discord.com/channels/189453139584221185/292281159495450625/1421431330440216696)

## Stack

Note the site uses the same stack (Flask, SQLAlchemy) as [CS139](https://warwick.ac.uk/fac/sci/dcs/teaching/modules/cs139/), to enable easy maintenance and development by most DCS students. Notably this means that there is no frontend framework (e.g. React, Vue) and the site is rendered server-side. Should this change in the future, the API is set up to partially support this (although it will probably need some tweaking). If some js is complex, I would reccomend using a pre-existing library (see bootstrap and tags) as this will make maintenance easier.

The only exception to this is the use of SCSS and bootstrap for styling. More info can be found in [Styling](#styling).

## File Structure

```
\
`- auth/
  `- api.py                     # authentication for api, also contains api key management endpoints
  `- oauth.py                   # intergration with UWCS keycloak; also exposes wrappers for requireing login/roles
`- events/
  `- api.py                     # wrapper for utils.py which exposes event management functionality to the api
  `- ui.py                      # wrapper for utils.py which exposes event management functionality to the website
  `- utils.py                   # functions for creating, modifying, deleting events; also handles week management
`- exec/
  `- publicity.py               # code for generating svg calendars for event publicity
  `- ui.py                      # exec dashboard endpoints
`- sass/
  `- bootstrap/                 # bootstrap scss files
  `- custom/                    # custom scss files
`- scripts/
  `- build_scss.py              # compiles scss files to static/css/main.css
  `- extract-phosphor.py        # extracts phosphor icon fonts and extract paths to icons.json
  `- import.py                  # imports events from the old stardust codebase into the database
  `- reset_db.py                # resets the database and (optionally) adds some test data
`- search/
  `- api.py                     # search api endpoints
  `- ui.py                      # search ui endpoints
  `- utils.py                   # actual code for searching events
`- static/
  `- css/                       # compiled css file
  `- fonts/                     # (non-phospohor) fonts
  `- icons/                     # phosphor icon fonts and css (generated by extract-phosphor.py) and custom svgs
  `- js/
    `- api-keys.js              # filtering and key creation for api keys page
    `- bootstrap.bundle.min.js  # bootstrap js file
    `- event-management.js      # validation and auto-filling for event creation/modification forms
    `- iframe.js                # js for enabling embedding of fulcrum in iframes
    `- search.js                # auto-suggest for search bar
    `- tags.min.js              # tag library for event tags (https://github.com/lekoala/bootstrap5-tags)
    `- theme-toggle.js          # dark/light mode toggle
`- templates/
  `- auth/
    `- keys.html                # api key management
  `- events/
    `- macros/                  # macros are jinja's version of subroutines
      `- filter.html            # filtering for events list
      `- list.html              # the list of events
      `- pill.html              # an event's display
    `- event.html               # a single event's page
    `- form.html                # event creation/modification form
    `- list.html                # a list of events
    `- tag.html                 # events associated with a tag
    `- tags.html                # all tags
  `- exec/
    `- dashboard.html           # exec dashboard
    `- publicity.html           # publicity generation page
  `- 403.html                   # 403 error
  `- 404.html                   # 404 error
  `- base.html                  # base template  
  `- previous.html              # events archive
  `- search.html                # search results
  `- upcoming.html              # upcoming events
`- volume/                      # contains database
`- .env                         # put environment variables here
`- config.py                    # shared variables used accross the app
`- DEVELOPER.md                 # hi 👋
`- DOCKERFILE                   # dockerfile for building a fulcrum container
`- fulcrum.py                   # main flask app
`- icons.json                   # paths for phosphor icons (generated by extract-phosphor.py)
`- LICENSE                      # MIT license
`- Pipfile                      # pipenv dependencies
`- Pipfile.lock                 # pipenv lockfile
`- README.md                    # main readme
`- ruff.toml                    # ruff config file
`- schema.py                    # database schema
`- swagger.json                 # swagger config
`- USER.md                      # user documentation
```

## Database schema

The database is defined in `schema.py` using SQLAlchemy.

It is fairly standard, with tables for Events, Tags, Weeks, and APIKeys.

The relationship between tagd and events is many to many and handles by the `event_tags` table. This allows for easier searching and filtering of events by tags.

Week and events is a one to many (a week can have many events, but an event can only be in one week). The relationship is done by a foreign key in both tables as this relationship is rarely used in the direction of week to events. It also means that the week in an event can be accessed by `event.week`.

## API

Fulcrum exposes an API at `/api/` that allows for event management for external applications. This exposes the same functionality as the website's UI, just in program-oriented format.

The API is documented at `/apidocs/` using [flasgger](https://github.com/flasgger/flasgger) and is automatically generated from docstrings in the code.

The endpoints that allow for the creation, modification, and deletion of events require authentication. This can either be done by:
- Loggining in via the website, which will set a session cookie (requires the user to be exec or sysadmin)
- Using the `Authorization` header with an API key. These can be generated and managed by execs at `/auth/keys/`

### Creating and managing API keys

API keys can be created and managed at `/auth/keys/`. This page requires the user to be logged in and to be exec or sysadmin.

An API key needs an owener (a string to identify who the key belongs to). Once created, the key will be shown once (so make sure to copy it down). The key can then be disabled or deleted at any time.

## Styling

[Bootstrap](https://getbootstrap.com/) is used for basic styling and responsiveness, it is reccomended to use this where possible to ensure consistency when styling. To update bootstrap, download the latest version SASS files from their website and replace the `sass/bootstrap/` directory. Furthermore, the newest version of bootstrap's js file should be added to `static/js/` and linked in `templates/base.html`.

If wanting to add custom styles, this site uses [SCSS](https://sass-lang.com/). This is an extention of CSS that allows for certain extra functionality, such as variables, selection, and other strcutures; however REGULAR CSS IS ALSO SUPPORTED. Custom styles should be added to the `sass/custom/` directory, and then imported into `sass/custom/_custom.scss`. It then needs to be compiled using `pipenv run python ./scripts/build_scss.py`, which will output to `static/css/main.css`. This is already linked in the base template, so no further action is needed.

## Icons

Icons are provided by [phosphor icons](https://phosphoricons.com/).

### Updating phosphor icons

These are continually updated and so the icons will need to be updated preiodically.
1. Download the latest version of phosphor icons from their website (https://phosphoricons.com/)
2. Extract the zip file and copy the entire folder to `scripts` directory
3. Run `pipenv run python ./scripts/extract-phosphor.py`. This will extract the necessary font files to `static/fonts/` and the paths to each icon to `icons.json`.

### Adding custom icons

Custom icons can be adding by placing an SVG file in `static/icons/` as `<name>.svg`. It can then be refrenced as `<name>`. Note the SVG should be a single path (i.e. no groups or multiple paths) so it will appear correctly in publicity.

## Colours

A colour map for common colours (for example `academic` and `social`) to hexcode is provided in `config.py` updating colours should be done here to ensure consistency accross the site.

## Warwick APIs

This system relies on 2 warwick APIs (although only one is being used at the moment)

### [Warwick Weeks](https://warwick.ac.uk/services/idg/services-support/web/tabula/api/timetabling/termweeks/)

This API provides the week numbering and start/end dates for each week in the academic year. It is imported once at the very start in the `config.py` file as when constantly requested it can be flaky. Note only the next year and 5 future years are imported, if the site is up for longer than this and never restarted, the weeks will not be up to date. The API goes back to 2006, events previous are hardcoded in `config.py` and provided curtosy of filmsoc.

### Warwick Map API

The code originally relied on the warwick map API to automatically fill in location URLs on events. However, warwick [recently changed its provider](https://warwick.ac.uk/services/estates/news/?newsItem=8ac672c69809ae5301981c55b2ab43f6). As part of this, the majority of info has been locked behind auth, and noone seems to either be willing or know how to give us an API key (this is in order to "prevent terrorism"). There seems to be some way to get a url link using estates redirects (https://discord.com/channels/189453139584221185/1047479520522928138/1411102186146107402) but we dont know how this works.

The old code for using the api is still in the relevant locations (`events/utils.py` and `static/js/event-management.js`) but it is currently commented out. If someone can figure out how to get this working, please do so.

## Testing

There is no automated testing because I don't know how to do it properly. Maybe someone can do this in the future?

## Ideas for the future

A list of some things that would be cool to add but would require more effort than I have time. See issues for the list of urgent requirements.

- [ ] Users table  
      Adding a users table would allow for a user's interactions to be tracked. Users will be able to sign on to an event and leave feedback. Exec can then see who is attending an event and be able to contact the attendees of event. Any changes to an event should also be emailed to attendees
- [ ] Testing  
      Currently the app has no automated testing. As a result it is likely that changes made may unintentionally affect other aspects of the app. Things that shpuld be tested are: api (all endpoints), utils (calling individual functions), and the ui displas events as expected
