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
