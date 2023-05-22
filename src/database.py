from datetime import datetime

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
    datetime = DateTimeField(required=True)

    ended = BooleanField(default=False)

    categories = ListField(StringField(required=True))

    distance = FloatField(required=True)

    price = IntField(required=True)

    participants = ListField(ReferenceField(User))


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
        date = datetime.today().date()
        logger.debug(f"Date wasn't specified. Using today's date: {date}.")

    ################################
    ##### ? PARTIALLY TESTED! ######
    ################################

    start = datetime.combine(date, datetime.min.time())
    end = datetime.combine(date, datetime.max.time())

    race = Race.objects(datetime__gte=start, datetime__lte=end).first()

    if race:
        logger.debug(f"Found race {race.name} between {start} and {end}. Date: {date}.")
    else:
        logger.debug(f"Can't find races between {start} and {end}. Date: {date}.")
    return race


async def get_future_race_by_name(name: str):
    logger.debug(f"Trying to find upcoming race with name {name}.")

    ################################
    #### ! WARNING! NOT TESTED! ####
    ################################

    race = Race.objects(name=name, datetime__gte=datetime.today()).first()

    if race:
        logger.debug(f"Race with name {name} is found.")
    else:
        logger.debug(f"Can't find upcoming race with name {name}.")

    return race


async def register_to_race(telegram_id, race_name):
    logger.debug(
        f"Trying to register user with telegram id {telegram_id} for race with name {race_name}."
    )

    ################################
    #### ! WARNING! NOT TESTED! ####
    ################################

    user = get_user(telegram_id)
    race = get_future_race_by_name(race_name)

    if user and race:
        race.participants.append(user)
        race.save()

        logger.debug(
            f"Successfully registered user with telegram id {telegram_id} for race with name {race_name}."
        )

        res = True
    else:
        logger.warning(
            f"Can't find either user with telegram id {telegram_id} or race with name {race_name}."
        )
        res = False
    return res


categories = ["М: CX / Gravel", "M: Road", "Ж: CX / Gravel", "Ж: Road"]
datetime = datetime.strptime("22.05.2023 20:00", "%d.%m.%Y %H:%M")


new_race = {
    "name": "Тестовая гонка",
    "datetime": datetime,
    "categories": categories,
    "distance": 50.2,
    "price": 1000,
}

# Race(**new_race).save()
