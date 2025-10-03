import re
from datetime import date, datetime, timedelta

from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from sqlalchemy import and_, func
from sqlalchemy.orm import foreign, reconstructor

from config import colours, custom_icons, icons

LONDON = timezone("Europe/London")

db = SQLAlchemy()


def initialise_db(app: Flask) -> None:
    """Initialises the database"""

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../volume/fulcrum.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # create the database tables
    with app.app_context():
        db.create_all()


class Week(db.Model):
    """Model for a week in the academic calendar"""

    __tablename__ = "weeks"

    id = db.Column(db.Integer, primary_key=True)

    # the start year of the academic year, for example 2022 for 2022-2023
    academic_year = db.Column(db.Integer, nullable=False)
    term = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)

    # store end dates as well, as they are useful for querying
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # enforce no duplicate weeks
    __table_args__ = (
        db.UniqueConstraint("academic_year", "term", "week", name="unique_week"),
    )

    # events in a week
    events = db.relationship(
        "Event",
        primaryjoin=lambda: db.and_(
            db.foreign(db.func.date(Event.start_time)) >= Week.start_date,
            db.foreign(db.func.date(Event.start_time)) <= Week.end_date,
        ),
        viewonly=True,
        lazy="dynamic",
    )

    def __init__(
        self, academic_year: int, term: int, week: int, start_date: date
    ) -> None:
        self.academic_year = academic_year
        self.term = term
        self.week = week
        self.start_date = start_date
        # end date is 6 days after the start date (counter-intuitive i know)
        self.end_date = start_date + timedelta(days=6)

    def __repr__(self) -> str:
        return (
            f"<Week {self.academic_year}-{self.term}-{self.week} "
            f"({self.start_date} to {self.end_date})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "academic_year": self.academic_year,
            "term": self.term,
            "week": self.week,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
        }


class Event(db.Model):
    """Model for an event"""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)

    # name and slug
    name = db.Column(db.String, nullable=False)
    slug = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)

    # whether the event is a draft
    draft = db.Column(db.Boolean, default=False)

    # location stuff
    location = db.Column(db.String, nullable=False)
    location_url = db.Column(db.String, nullable=True)

    # visual stuff
    icon = db.Column(db.String, nullable=True)
    colour = db.Column(db.String, nullable=True)

    # time stuff
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    # week relationship
    week = db.relationship(
        "Week",
        primaryjoin=and_(
            foreign(func.date(start_time)) >= func.date(Week.start_date),
            foreign(func.date(start_time)) <= func.date(Week.end_date),
        ),
        viewonly=True,
        uselist=False,
        lazy="joined",
    )

    # tags relationship
    tags = db.relationship(
        "Tag", secondary="event_tags", backref=db.backref("events", lazy=True)
    )

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        description: str,
        draft: bool,
        location: str,
        location_url: str | None,
        icon: str | None,
        colour: str | None,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        self.name = name
        self.slug = name.lower().replace(" ", "-")
        self.description = description
        self.draft = draft
        self.location = location
        self.location_url = location_url
        self.icon = icon
        self.colour = colour if colour else "blue"
        self.start_time = start_time
        self.end_time = end_time
        self._localise_times()

    @reconstructor
    def reinit(self) -> None:
        """
        Localise start and end times on db load
        Previously only happened in __init__ ie only new instantiations
        Removes need to remember to manually localise everywhere
        """

        self._localise_times()

    def _localise_times(self) -> None:
        """
        Helper to localise start and end times of events

        Only localise if not already tz-aware - allows external localisation

        For tz-aware DB, harden to strictly enforce 'Europe/London' e.g.
        ```
        self.end_time.tzinfo.zone == LONDON.zone
        ```
        None is fine rn and cleaner
        Use localize instead of .replace to avoid LMT offset issue

        Should not need to localise start_time or end_time outside this
        """

        self.start_time = LONDON.localize(self.start_time) \
                                            if self.start_time.tzinfo is None \
                                            else self.start_time
        self.end_time = LONDON.localize(self.end_time) \
                                            if self.end_time.tzinfo is None \
                                            else self.end_time

    def __repr__(self) -> str:
        return (
            f"<Event {self.name} (ID: {self.id}) "
            f"at {self.location} on {self.start_time}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "draft": self.draft,
            "location": self.location,
            "location_url": self.location_url,
            "icon": self.icon,
            "colour": self.colour,
            "start_time": self.start_time.isoformat("T", "minutes"),
            "end_time": self.end_time.isoformat("T", "minutes"),
            "week": self.week.to_dict() if self.week else None,
            "tags": [tag.to_dict() for tag in self.tags],  # type: ignore
            "url": (
                url_for(
                    "events_ui.view",
                    year=self.week.academic_year,
                    term=self.week.term,
                    week=self.week.week,
                    slug=self.slug,
                    _external=True,
                )
                if self.week
                else None
            ),
        }

    def validate(self) -> str | None:
        """Validates an event's data"""

        # check if required fields are filled
        for field in ["name", "description", "location"]:
            if getattr(self, field) == "":
                return f"{field.capitalize()} is required"

        if self.end_time < self.start_time:
            return "End time cannot be before start time"

        # check if colour is valid
        colour_regex = re.compile(r"^#[0-9a-fA-F]{6}$")
        if self.colour and (
            not colour_regex.match(self.colour) and self.colour not in colours
        ):
            return "Colour must be a valid hex code or one of: " + ", ".join(colours)

        # check if icon is valid
        if self.icon and self.icon.removeprefix("ph-") not in icons:
            return (
                "Icon must be a phosphor icon (https://phosphoricons.com/) or one of: "
                + ", ".join(custom_icons)
            )

        return None


class Tag(db.Model):
    """Model for a single tag"""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    def __init__(self, name: str) -> None:
        self.name = name.lower()

    def __repr__(self) -> str:
        return f"<Tag {self.name} (ID: {self.id})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }


event_tags = db.Table(
    "event_tags",
    db.Column("event_id", db.Integer, db.ForeignKey("events.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class APIKey(db.Model):
    """Model for an API key"""

    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String, unique=True, nullable=False)
    owner = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)

    def __init__(self, key_hash: str, owner: str) -> None:
        self.key_hash = key_hash
        self.owner = owner
        self.created_at = datetime.now(LONDON)
        self.active = True

    def __repr__(self) -> str:
        return f"<APIKey {self.key_hash} (ID: {self.id}) owned by {self.owner}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key_hash": self.key_hash,
            "owner": self.owner,
            "created_at": self.created_at.isoformat("T", "minutes"),
            "active": self.active,
        }

    def deactivate(self) -> None:
        """Deactivate the API key"""
        self.active = False
        db.session.commit()

    def activate(self) -> None:
        """Activate the API key"""
        self.active = True
        db.session.commit()
