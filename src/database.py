from datetime import datetime, timedelta
from collections import namedtuple

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
                "race_number": StringField(default="N/A"),
            },
        )
    )

    ended = BooleanField(default=False)


class Payment(Document):
    telegram_id = IntField(required=True)
    race = ReferenceField(Race, required=True)
    price = IntField(required=True)
    date = DateTimeField(required=True)

    verified = BooleanField(default=False)


async def get_payment(telegram_id, race):
    payment = Payment.objects(telegram_id=telegram_id, race=race).first()
    return payment


async def new_payment(telegram_id, race, price):
    date = get_day().now

    payment = {
        "telegram_id": telegram_id,
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


async def get_user_by_fatracing_id(fatracing_id):
    return User.objects(fatracing_id=fatracing_id).first()


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

    logger.debug(f"Trying to get list of upcoming races after {day.now}.")

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
        "race_number": "N/A",
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

        await new_payment(telegram_id, race, race.price)

        res = True
    else:
        logger.warning(
            f"Can't find either user with telegram id {telegram_id} or race with name {race_name}."
        )
        res = False
    return res


def get_day(dt: str = None):
    Day = namedtuple("Day", ["begin", "now", "end"])

    if not dt:
        dt = datetime.now() + timedelta(hours=g.HOUR_SHIFT)
    else:
        dt = datetime.strptime(f"{dt} 00:00", "%d.%m.%Y %H:%M")

    dts = datetime.combine(dt, datetime.min.time())
    dte = datetime.combine(dt, datetime.max.time())

    day = Day(dts, dt, dte)

    return day


categories = ["М: CX / Gravel", "М: Road", "Ж: CX / Gravel", "Ж: Road"]
start = datetime.strptime("27.05.2023 23:50", "%d.%m.%Y %H:%M") + timedelta(
    hours=g.HOUR_SHIFT
)


TDS_COORDS = [58.649757, 31.459013]
TDS_CODE = "TDS"

TEST_COORDS = [36.629652557353594, 31.775350128089276]
TEST_CODE = "TEST"

new_race = {
    "name": "TEST",
    "start": start,
    "location": TEST_COORDS,
    "code": TEST_CODE,
    "categories": categories,
    "distance": 50.2,
    "price": 1000,
}

# Race(**new_race).save()
