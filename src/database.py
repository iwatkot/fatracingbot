from datetime import datetime

from mongoengine import (
    connect,
    Document,
    StringField,
    IntField,
    ListField,
    FloatField,
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
    birthday = StringField(required=True)

    email = StringField()
    phone = StringField()


class Race(Document):
    name = StringField(required=True)
    date = StringField(required=True)
    time = StringField(required=True)

    categories = ListField(StringField(required=True))

    distance = FloatField(required=True)

    price = IntField(required=True)


async def get_user(telegram_id):
    user = User.objects(telegram_id=telegram_id).first()

    if user:
        logger.debug(f"User with telegram id {telegram_id} is found in the database.")
    else:
        logger.debug(
            f"User with telegram id {telegram_id} wasn't found in the database."
        )

    return user


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


async def get_race_by_date(date: datetime.date = None):
    if not date:
        date = datetime.today().strftime("%d.%m.%Y")
    logger.debug(f"Trying to find event for date: {date}.")

    race = Race.objects(date=date).first()

    if race:
        logger.debug(f"Found a {race.name} event for date: {date}.")
    else:
        logger.debug(f"Didn't find any event for date: {date}.")

    return race


categories = ["М: CX / Gravel", "M: Road", "Ж: CX / Gravel", "Ж: Road"]


new_race = {
    "name": "Тестовая гонка",
    "date": "22.05.2023",
    "time": "14:00",
    "categories": categories,
    "distance": 50.2,
    "price": 1000,
}

# Race(**new_race).save()
