import os

from datetime import datetime
from collections import namedtuple

from django.conf import settings

import pandas as pd

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
    SequenceField,
)

EXCEL_PATH = os.path.join(settings.APP_STATIC_DIR, "participants.xlsx")


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


class Payment(Document):
    payment_id = SequenceField(sequence_name="payment_id", required=True, unique=True)

    telegram_id = IntField(required=True)
    full_name = StringField(required=True)
    race = ReferenceField(Race, required=True)
    price = IntField(required=True)
    date = DateTimeField(required=True)

    verified = BooleanField(default=False)


def get_payment_status(race: Race, telegram_id: int) -> bool | None:
    payment = Payment.objects(race=race, telegram_id=telegram_id).first()
    if payment:
        return payment.verified


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


def get_races(status: str):
    day = get_day()

    if status == "upcoming":
        races = Race.objects(start__gte=day.now).order_by("start")
    elif status == "ended":
        races = Race.objects(start__lte=day.now).order_by("-start")

    return races


def create_participants_table(race):
    participants = race.participants
    participants_infos = race.participants_infos

    table_entries = []
    for participant, participant_info in zip(participants, participants_infos):
        telegram_id = participant.telegram_id
        payment_status = get_payment_status(race, telegram_id)
        if payment_status:
            payment_status = "Оплачено"
        else:
            payment_status = "Не оплачено"

        entry = {
            "Номер": participant_info["race_number"],
            "Пол": participant.gender,
            "Дата рождения": participant.birthday.strftime("%d.%m.%Y"),
            "Категория": participant_info["category"],
            "Полное имя": f"{participant.last_name} {participant.first_name}",
            "Telegram ID": participant.telegram_id,
            "Телефон": participant.phone,
            "Email": participant.email,
            "Оплата": payment_status,
        }
        table_entries.append(entry)

    table_entries = sorted(table_entries, key=lambda x: x["Номер"])

    df = pd.DataFrame(table_entries)
    df.to_excel(EXCEL_PATH, index=False)

    return EXCEL_PATH
