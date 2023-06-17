from datetime import datetime
from collections import namedtuple

from mongoengine import (
    Document,
    IntField,
    StringField,
    DateField,
    DateTimeField,
    ListField,
    FloatField,
    BooleanField,
    ReferenceField,
    DictField,
)


class User(Document):
    telegram_id = IntField(required=True, unique=True)

    first_name = StringField(required=True)
    last_name = StringField(required=True)

    gender = StringField(required=True)
    birthday = DateField(required=True)

    email = StringField()
    phone = StringField()


class Race(Document):
    name = StringField(required=True)
    start = DateTimeField(required=True)
    location = ListField(FloatField(required=True), required=True)

    code = StringField(required=True)

    categories = ListField(StringField(required=True))

    distance = FloatField(required=True)

    price = IntField(required=True)

    registration_open = BooleanField(default=True)

    participants = ListField(ReferenceField(User))
    participants_infos = ListField(
        DictField(
            fields={
                "telegram_id": IntField(required=True),
                "category": StringField(required=True),
                "race_number": IntField(default=0),
            },
        )
    )

    ended = BooleanField(default=False)


def create_race(form_data):
    new_race = {
        "name": form_data["name"],
        "start": form_data["start"],
        "location": [location.strip() for location in form_data["location"].split(",")],
        "code": form_data["code"],
        "categories": [
            category.strip() for category in form_data["categories"].split(",")
        ],
        "distance": form_data["distance"],
        "price": form_data["price"],
        "registration_open": form_data["registration_open"],
    }

    Race(**new_race).save()


def get_day(dt: str = None):
    Day = namedtuple("Day", ["begin", "now", "end"])

    if not dt:
        dt = datetime.utcnow()
    else:
        dt = datetime.strptime(f"{dt} 00:00", "%d.%m.%Y %H:%M")

    dts = datetime.combine(dt, datetime.min.time())
    dte = datetime.combine(dt, datetime.max.time())

    day = Day(dts, dt, dte)

    return day
