import datetime

import pytz
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, func

db = SQLAlchemy()


def initialise_db(app: Flask) -> None:
    """Initialises the database for events"""

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///volume/events.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # create the database tables if they don't exist
    with app.app_context():
        db.create_all()


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
    end_time = db.Column(db.DateTime, nullable=True)

    # week relationship
    date = db.relationship(
        "Week",
        primaryjoin=and_(
            func.date(start_time) >= func.date(Week.start_date),  # type: ignore  # noqa: F821
            func.date(start_time) <= func.date(Week.end_date),  # type: ignore  # noqa: F821
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
        start_time: datetime.datetime,
        end_time: datetime.datetime | None,
    ) -> None:
        self.name = name
        self.slug = name.lower().replace(" ", "-")
        self.description = description
        self.draft = draft
        self.location = location
        self.location_url = location_url
        self.icon = icon
        self.colour = colour
        # ensure times are london-time
        self.start_time = start_time.astimezone(pytz.timezone("Europe/London"))
        self.end_time = (
            end_time.astimezone(pytz.timezone("Europe/London")) if end_time else None
        )

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
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "date": {
                "year": self.date.academic_year,
                "term": self.date.term,
                "week": self.date.week,
            },
            "tags": [tag.name for tag in self.tags.all()],
        }


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

    def __init__(
        self, academic_year: int, term: int, week: int, start_date: datetime.date
    ) -> None:
        self.academic_year = academic_year
        self.term = term
        self.week = week
        self.start_date = start_date
        # end date is 6 days after the start date (counter-intuitive i know)
        self.end_date = start_date + datetime.timedelta(days=6)

    def __repr__(self) -> str:
        return (
            f"<Week {self.academic_year}-{self.term}-{self.week} "
            f"({self.start_date} to {self.end_date})>"
        )


class Tag(db.Model):
    """Model for a single tag"""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<Tag {self.name} (ID: {self.id})>"


event_tags = db.Table(
    "event_tags",
    db.Column("event_id", db.Integer, db.ForeignKey("events.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class APIKey(db.Model):
    """Model for an API key"""

    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False)
    owner = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)

    def __init__(self, key: str, owner: str) -> None:
        self.key = key
        self.owner = owner
        self.created_at = datetime.datetime.now(pytz.timezone("Europe/London"))
        self.active = True

    def __repr__(self) -> str:
        return f"<APIKey {self.key} (ID: {self.id}) owned by {self.owner}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "owner": self.owner,
            "created_at": self.created_at.isoformat(),
            "active": self.active,
        }

    def deactivate(self) -> None:
        """Deactivate the API key"""
        self.active = False
        db.session.commit()
