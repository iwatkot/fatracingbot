import os
import csv
import tarfile
import shutil

from datetime import datetime
from collections import namedtuple, defaultdict

import pandas as pd

from mongoengine import (
    connect,
    Document,
    StringField,
    IntField,
    ListField,
    FloatField,
    DateField,
    DateTimeField,
    ReferenceField,
    BooleanField,
    DictField,
    SequenceField,
)

import globals as g

logger = g.Logger(__name__)

cinfo = connect(
    host=g.AppState.DataBase.host,
    port=g.AppState.DataBase.port,
    db=g.AppState.DataBase.db,
    username=g.AppState.DataBase.username,
    password=g.AppState.DataBase.password,
)

logger.info(
    f"Connection to MongoDB databases {cinfo.list_database_names()} is established."
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


class Payment(Document):
    payment_id = SequenceField(sequence_name="payment_id", required=True, unique=True)

    telegram_id = IntField(required=True)
    full_name = StringField(required=True)
    race = ReferenceField(Race, required=True)
    price = IntField(required=True)
    date = DateTimeField(required=True)

    verified = BooleanField(default=False)


async def get_payment(telegram_id, race):
    payment = Payment.objects(telegram_id=telegram_id, race=race).first()
    return payment


async def verify_payment(payment_id):
    payment = Payment.objects(payment_id=payment_id).first()
    payment.update(verified=True)
    payment.save()

    return payment


async def get_unverified_payments():
    payments = Payment.objects(verified=False)
    return payments


async def new_payment(telegram_id, full_name, race, price):
    date = get_day().now

    payment = {
        "telegram_id": telegram_id,
        "full_name": full_name,
        "race": race,
        "price": price,
        "date": date,
    }

    Payment(**payment).save()


async def get_user(telegram_id):
    user = User.objects(telegram_id=telegram_id).first()

    if user:
        logger.debug(f"User with telegram id {telegram_id} is found in the database.")
    else:
        logger.debug(
            f"User with telegram id {telegram_id} wasn't found in the database."
        )

    return user


async def get_participant_info(race, telegram_id):
    for participant_info in race.participants_infos:
        if participant_info["telegram_id"] == telegram_id:
            return participant_info["category"], participant_info["race_number"]


async def get_participant_by_race_number(race, race_number):
    for participant, participant_info in zip(
        race.participants, race.participants_infos
    ):
        if int(participant_info["race_number"]) == race_number:
            return participant, participant_info["category"]


async def update_user(telegram_id, **kwargs):
    user = User.objects(telegram_id=telegram_id).first()

    if user:
        logger.debug(
            f"User with telegram id {telegram_id} is found in the database. "
            f"Trying to update the user with data: {kwargs}."
        )
        user.update(**kwargs)
        user.reload()

        logger.debug(f"User with telegram id {telegram_id} successfully updated.")
    else:
        logger.warning(
            f"User with telegram id {telegram_id} wasn't found in the database."
        )

    return user


async def new_user(**kwargs):
    logger.debug(f"Trying to create a new user with data: {kwargs}.")
    return User(**kwargs).save()


async def get_upcoming_races():
    day = get_day()

    logger.debug(f"Trying to get list of upcoming races after {day.begin}.")

    races = Race.objects(start__gte=day.now).order_by("start")

    logger.debug(f"Found {len(races)} races after {day.now}.")

    return races


async def get_race_by_date(day: str = None):
    if not day:
        day = get_day()
    else:
        day = get_day(day)

    race = Race.objects(start__gte=day.begin, start__lte=day.end).first()

    if race:
        logger.debug(f"Found race {race.name} between {day.begin} and {day.end}.")
    else:
        logger.debug(f"Can't find races between {day.begin} and {day.end}.")
    return race


async def get_upcoming_race_by_name(name: str):
    logger.debug(f"Trying to find upcoming race with name {name}.")

    day = get_day()

    race = Race.objects(name=name, start__gte=day.now).first()

    if race:
        logger.debug(f"Race with name {name} is found.")
    else:
        logger.debug(f"Can't find upcoming race with name {name}.")

    return race


async def register_to_race(telegram_id, race_name, category):
    logger.debug(
        f"Trying to register user with telegram id {telegram_id} for race with name {race_name} "
        f"and category {category}."
    )

    user = await get_user(telegram_id)

    participant_info = {
        "telegram_id": telegram_id,
        "category": category,
        "race_number": 0,
    }

    logger.debug(f"Prepared participant info: {participant_info}.")

    race = await get_upcoming_race_by_name(race_name)

    if user and race:
        race.participants.append(user)
        race.participants_infos.append(participant_info)
        race.save()

        logger.debug(
            f"Successfully registered user with telegram id {telegram_id} for race with name {race_name}. "
            f"in category {category}."
        )

        full_name = f"{user.last_name} {user.first_name}"

        await new_payment(telegram_id, full_name, race, race.price)

        res = True
    else:
        logger.warning(
            f"Can't find either user with telegram id {telegram_id} or race with name {race_name}."
        )
        res = False
    return res


async def open_registration(race):
    logger.info(f"Trying to open race with name {race.name}.")

    race.update(registration_open=True)
    race.save()


async def close_registration(race):
    logger.info(f"Trying to close race with name {race.name}.")

    race.update(registration_open=False)
    race.save()

    categories = race.categories
    participant_infos = race.participants_infos

    logger.info(
        f"Race has {len(categories)} categories and {len(participant_infos)} participants."
    )
    race_number_data = defaultdict(list)
    category_prefix = 1
    for category in categories:
        participant_number = 1
        participants_by_category = [
            participant
            for participant in participant_infos
            if participant["category"] == category
        ]
        for participant in participants_by_category:
            race_number = f"{category_prefix}{str(participant_number).zfill(2)}"
            participant["race_number"] = int(race_number)
            participant_number += 1
            race_number_data[category].append(race_number)
        category_prefix += 1

    race.save()

    logger.info(
        f"Closed registration and generate race numbers for {len(race_number_data)} categories."
    )

    return race_number_data


async def create_participants_table(race):
    participants = race.participants
    participants_infos = race.participants_infos

    table_entries = []
    for participant, participant_info in zip(participants, participants_infos):
        entry = {
            "Номер": participant_info["race_number"],
            "Пол": participant.gender,
            "Дата рождения": participant.birthday.strftime("%d.%m.%Y"),
            "Категория": participant_info["category"],
            "Полное имя": f"{participant.last_name} {participant.first_name}",
            "Telegram ID": participant.telegram_id,
            "Телефон": participant.phone,
            "Email": participant.email,
        }
        table_entries.append(entry)

    table_entries = sorted(table_entries, key=lambda x: x["Номер"])

    df = pd.DataFrame(table_entries)
    os.makedirs(g.TMP_DIR, exist_ok=True)
    excel_path = os.path.join(g.TMP_DIR, "participants.xlsx")

    df.to_excel(excel_path, index=False)

    return excel_path


def get_day(dt: str = None):
    Day = namedtuple("Day", ["begin", "now", "end"])

    if not dt:
        dt = datetime.utcnow()

        logger.debug(f"Date is not specified, using current UTC time for now: {dt}.")
    else:
        dt = datetime.strptime(f"{dt} 00:00", "%d.%m.%Y %H:%M")

    dts = datetime.combine(dt, datetime.min.time())
    dte = datetime.combine(dt, datetime.max.time())

    day = Day(dts, dt, dte)

    return day


name = "Тур де Селищи"
categories = [
    "М: ШОССЕ",
    "Ж: ШОССЕ",
    "М: ЦК",
    "Ж: ЦК",
    "М: ФИКС СИНГЛ",
    "Ж: ФИКС СИНГЛ",
    "М: МТБ",
    "Ж: МТБ",
]
start = datetime.strptime("07.06.2023 20:00", "%d.%m.%Y %H:%M")
location = [58.64975393131507, 31.458961915652303]
code = "TDS"
distance = 125
price = 1000

new_race = {
    "name": name,
    "start": start,
    "location": location,
    "code": code,
    "categories": categories,
    "distance": distance,
    "price": price,
}

# Race(**new_race).save()


# @crontab("0 1 * * *")
async def backup():
    collection_names = sorted(
        cinfo.get_database(g.AppState.DataBase.db).list_collection_names()
    )
    collections = [Payment, Race, User]

    if not len(collection_names) == len(collections):
        logger.error(
            "Created collections and collection names are not equal, backup stopped."
        )
        return

    logger.info(f"Starting backup for collections: {collection_names}.")

    TMP_DIR = os.path.join(g.WORKSPACE_PATH, "tmp")
    BACKUP_DIR = os.path.join(TMP_DIR, "backup")
    os.makedirs(BACKUP_DIR, exist_ok=True)

    for cname, cclass in zip(collection_names, collections):
        logger.debug(f"Downloading collection {cname}.")

        collection_path = os.path.join(BACKUP_DIR, cname)
        os.makedirs(collection_path, exist_ok=True)
        for document in cclass.objects:
            document_path = os.path.join(collection_path, f"{document.id}.csv")
            document_json = dict(document.to_mongo())
            with open(document_path, "w") as f:
                writer = csv.DictWriter(f, document_json.keys())
                writer.writeheader()
                writer.writerow(document_json)

    logger.debug("Downloaded all documents in CSV format.")

    tar_path = os.path.join(TMP_DIR, "backup.tar")

    with tarfile.open(tar_path, "w") as tar:
        tar.add(BACKUP_DIR, arcname="backup")

    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # TODO: somehow handle the backup file

    shutil.rmtree(TMP_DIR)
