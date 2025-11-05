# User documentation for fulcrum

If you are a developer or want to use the API, see [DEVELOPER.md](DEVELOPER.md) instead.

## Viewing events

An event's permalink can be found by `/<academic_year>/<term>/<week>/<slug>/`. A slug is a URL friendly version of the event name, with spaces replaced by hyphens and all characters lowercased. For example, an event called "My Event" in week 1 of term 1 of the 2023-2024 academic year would have the permalink `/2023/1/1/my-event/`.

## Authentication

To do anything documented below, you need to be logged in. The site is intergrated with UWCS auth, so you can use your warwick ITS credentials to log in. You then need to be either exec or sysadmin on keycloak to be able to do anything. An easy way to see if you're logged in correctly is that the navbar has a yellow bottom navigation bar when you're logged in.

## [Creating events](https://events.uwcs.co.uk/create/)

Note enabling javascript will make this process much easier as validation will be done client side

### Name (Required)

The name of the event. This is required, and should be a short but descriptive name for the event. Note needs to be unique within the week.

### Draft

Whether the event is a draft or not. Draft events are not visible to anyone except exec and sysadmin, and do not appear in the main list of events. This is useful for creating events that you want to work on later, or for events that are not yet ready to be published.

### Description (Required)

A description of the event. This can be as long as you like. This field supports [markdown](https://www.markdownguide.org/cheat-sheet/) for formatting.

### Location (Required)

Where the event is taking place.

### Location URL

A link to where the event is taking place. It should be used when the event is at a location off campus.

### Event Icon

An icon for the event. Where possible, use a [phosphor icon](https://phosphoricons.com/). If a custom icon is required, follow the instructions in [DEVELOPER.md](DEVELOPER.md#adding-custom-icons) to add one. When typing, custom icons will appear as suggestions.

### Event Colour

The colour used when displaying the event, will also be used as its category. Where possible use a pre-defined colour (such as academic, social, gaming, etc) a full list of custom colours is in `config.py`. If none are suitable, use a 6 digit hex code (without the #). 

### Tags

The tags for an event. These should be general (such as "talk", "fng", etc). If possible use pre-existing tags which should appear as suggestions when typing. Tags are not case sensitive, and will be converted to lowercase.

### Start Time (Required)

When the event starts. This is required, and should be in the format `YYYY-MM-DD HH:MM` in 24 hour time. The timezone is assumed to be Europe/London.

### End Time (Required)

When the event ends. This is required, and should be in the format `YYYY-MM-DD HH:MM` in 24 hour time. The timezone is assumed to be Europe/London. The end time must be after the start time.

### Duration

If easier, you can specify the duration of the event intead of the end time. It should be in the format `DD:HH:MM`. This will automatically set the end time based on the start time.

### Repeat Events

If an event is a recurring event, you can account for this using the `add time` button. This will add another set of start and end time fields. By default, new times will be set to one week after the previous time, but this can be changed. End-times can also be set and automatically calculated. Editing one end time or the duration will update all end times to match. You can also remove times using the `remove` button next to each time.

## Editing events

An event can be edited by going to its permalink and clicking the edit button in the top right. This will take you to the same form as creating an event, but with all fields pre-filled. You can then edit any field and save the event.

## Deleting events

Follow the steps to edit an event, but once in the edit form scroll to the bottom and click the delete button. Confirm your chouse and the event will be deleted. THIS CANNOT BE UNDONE.

## [iCal](https://events.uwcs.co.uk/uwcs.ics)

An ical feed for all events is available at `/uwcs.ics`. This can be added to any calendar application that supports ical feeds, such as Google Calendar or Outlook. Note that the feed is read-only, and any changes made to events on the site will be reflected in the feed.

## [Publicity](https://events.uwcs.co.uk/exec/publicity/)

An exec-only endpoint for creating single week calendars is available at `/exec/publicity/`.

### Single week calendar

Select a `year` and `term` from the dropdowns and then a `week`. You do not need to change `End Week` as this will be prefilled. Then click generate to create an svg of the calender for that week. Note there is a limit of 8 events in a week with a max of 6 events in a single day. If the week exeeds this, publicity will have to be done manually.

If the generated SVG looks good, it can be downloaded direct to PNG via the `Save PNG` button. If frther editing is required, click `Copy SVG` to copy the SVG to your clipboard and paste it into a vector graphics editor such as Figma.

### Multi week calendar

Same as single week calendar, but select a different `End Week`. Note if more than 4 events are in a single day, only the first 4 will be shown.