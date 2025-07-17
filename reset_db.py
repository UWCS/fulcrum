import os
import sys
from datetime import date, datetime, timedelta

import pytz
from werkzeug.security import generate_password_hash

from fulcrum import app
from schema import APIKey, Event, Tag, Week, db


def reset_database(seed: bool) -> None:
    with app.app_context():
        # delete all tables
        db.drop_all()
        db.create_all()

        # seed data
        if seed:
            # create dummy event
            start_time = datetime(
                2025, 9, 30, 12, 0, 0, tzinfo=pytz.timezone("Europe/London")
            )
            dummy_event = Event(
                name="Test Event",
                description="This is a test description for the test event",
                draft=False,
                location="Test Location",
                location_url="https://example.com",
                icon="ph-test-tube",
                colour="social",
                start_time=start_time,
                end_time=start_time + timedelta(hours=1),
            )
            db.session.add(dummy_event)
            db.session.commit()

            # create dummy week (welcome week 2025)
            dummy_week = Week(
                academic_year=2025,
                term=1,
                week=0,
                start_date=date(2025, 9, 29),
            )
            db.session.add(dummy_week)
            db.session.commit()

            # create dummy tags
            dummy_tag1 = Tag("test")
            dummy_tag2 = Tag("tag")
            db.session.add(dummy_tag1)
            db.session.add(dummy_tag2)
            db.session.commit()

            # associate dummy event with dummy tags
            dummy_event.tags.append(dummy_tag1)
            dummy_event.tags.append(dummy_tag2)
            db.session.commit()

        # create dummy API key
        api_key = APIKey(
            generate_password_hash(str(os.getenv("API_KEY"))), "import-script"
        )
        db.session.add(api_key)
        db.session.commit()


if __name__ == "__main__":
    print("Resetting database...")
    seed = sys.argv[1].lower() == "seed" if len(sys.argv) > 1 else False
    reset_database(seed)
    print("done :)")
