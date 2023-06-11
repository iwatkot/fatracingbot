from enum import Enum
from re import escape


class Messages(Enum):
    START = (
        "Привет! Это официальный Telegram бот FATRACING.\n"
        "Он позволяет регистрироваться на гонки, а также получать информацию о них.\n"
        "Помимо этого с помощью бота вы можете получить доступ к своим "
        "результатам на состоявшихся мероприятиях.\n\n"
        "Пожалуйста, воспользуйтесь меню для регистрации, если вы этого еще не сделали. Это займет всего минуту."
    )

    MENU_CHANGED = "Вы перешли в раздел  `{}`"

    REG_FIRST_NAME = "Пожалуйста, введите ваше имя. Это обязательное поле."
    REG_LAST_NAME = "Пожалуйста, введите вашу фамилию. Это обязательное поле."
    REG_GENDER = "Пожалуйста, укажите ваш пол. Это обязательное поле."
    REG_BIRTHDAY = "Пожалуйста, введите вашу дату рождения в формате `ДД.ММ.ГГГГ`. Это обязательное поле."
    REG_EMAIL = "Пожалуйста, введите вашу электронную почту. Это необязательное поле."
    REG_PHONE = "Пожалуйста, введите ваш номер телефона в формате `+7XXXXXXXXXX`. Это необязательное поле."

    REG_CANCELLED = "Регистрация отменена."
    REG_SUCCESS = "Регистрация успешно завершена. Спасибо!"
    WRONG_GENDER = "Неверный формат. Пожалуйста, введите ваш пол."
    WRONG_EMAIL = "Неверный формат. Пожалуйста, введите вашу электронную почту."
    WRONG_NAME = "Неверный формат. Пожалуйста, введите ваше имя."
    WRONG_BIRTHDAY = "Неверный формат. Пожалуйста, введите вашу дату рождения."
    WRONG_PHONE = "Неверный формат. Пожалуйста, введите ваш номер телефона."

    USER_INFO = (
        "`Имя:` {first_name}\n`Фамилия:` {last_name}\n"
        "`Пол:` {gender}\n`Дата рождения:` {birthday}\n"
        "`Email:` {email}\n`Телефон:` {phone}\n"
    )

    EDIT_CANCELLED = "Редактирование отменено."
    EDIT_SUCCESS = "Редактирование успешно завершено."

    NO_RACE = "Сегодня не проводится ни одной гонки."

    ONLY_FOR_REGISTERED = "Эта функция доступна только зарегистрированным участникам."
    ONLY_FOR_PARTICIPANTS = (
        "Эта функция доступна только участникам гонки. "
        "Вы не найдены в списке участников."
    )

    TRANSLATION_REQUEST = (
        "\n\nМы  `убедительно просим`  всех участников  `включить трансляцию геолокации`  на время гонки. "
        "Благодаря этому зрители смогут следить за положением гонщиков на "
        "карте в реальном времени. Помимо этого, в случае возникновения "
        "проблем, организаторы смогут быстрее оказать вам помощь.\n\n"
        "Большое спасибо."
    )

    TRANSLATION_TOOLTIP = (
        "Пожалуйста, убедитесь что Telegram на вашем устройстве, может  получать вашу геолокацию в  `фоновом режиме`. "
        "После этого начните трансляцию геолокации для бота.\n"
        "Бот ответит вам только на начало трансляции, затем данные будут использованы для обновления "
        "вашего положения на карте и таблице лидеров."
    )
    TRANSLATION_LIVE = (
        "Бот начал получать ваши геоданные. Убедитесь, что Telegram может получать вашу "
        "геолокацию в  `фоновом режиме`  и  `не отключайте трансляцию`  до окончания гонки. Спасибо."
    )
    TRANSLATION_NOT_LIVE = (
        "Вы прислали боту свое местоположение, но  `не включили трансляцию`  геолокации. "
        "Пожалуйста, включите трансляцию геолокации, иначе бот не сможет получать ваши данные."
    )

    NO_EVENTS = "В ближайшее время не запланировано ни одной гонки."
    RACE_INFO = (
        "`{name}`\n\nСтарт:  `{start}`\nДистанция:  `{distance} км`\n"
        "Категории:  {categories}"
    )

    PAYMENT_INSTRUCTIONS = (
        "Вы добавлены в список участников гонки.\n"
        "Пожалуйста,  `оплатите участие`  в гонке, в противном случае мы не гарантируем наличие доступного слота.\n\n"
        "Сумма к оплате:  `{price}`\nНомер телефона для СБП:  `{phone}`\n"
        "Список банков:  `{banks}`\nПолучатель:  `{cred}`\n\n"
        "Вы получите сообщение от бота, когда платеж будет подтвержден. "
        "Обратите внимание, что платежи обрабатываются в ручном режиме, подтверждение может занять некоторое время."
    )

    HELP_WITH_COORDS = (
        "Бот уже знает ваше местоположение, пожалуйста кратко сообщите что у вас случилось. "
        "Ваше сообщение с координатами будет отправлено организаторам и мы постараемся помочь вам как можно скорее."
    )

    HELP_NO_COORDS = ""  # TODO: Add text.

    SOS_MESSAGE = (
        "🚨 Поступил запрос помощи.\n\nTelegram username: {telegram_username}\n"
    )

    ADMIN_RACE_STARTED = (
        "🏁 Информация о гонке сохранена, статус гонки успешно изменен на активный."
    )
    ADMIN_NO_ACTIVE_RACE = "🚫 Нет активных гонок."
    ADMIN_RACE_END = "✅ Статус гонки успешно изменен на завершенный, трансляция геолокации остановлена."

    ADMIN_TIMEKEEPING_INIT = (
        "ℹ️ Включен режим записи результатов на финише. Бот будет ожидать сообщения с номером участника, "
        "любые другие данные будут проигнорированы. Время будет подсчитано автоматически с момента старта гонки. "
        "Чтобы выйти из режима, нажмите кнопку  `Завершить`. Вы сможете вернуться в этот режим в любой момент."
    )

    def format(self, *args, **kwargs):
        return escape(self.value.format(*args, **kwargs))

    def escaped(self):
        return escape(self.value)


class Buttons(Enum):
    # * Context buttons.
    BTN_CANCEL = "Отмена"
    BTN_COMPLETE = "Завершить"
    BTN_SKIP = "Пропустить"
    BTN_CONFIRM = "Подтвердить"
    BTN_GENDER_M = "Мужской"
    BTN_GENDER_F = "Женский"
    GENDERS = [BTN_GENDER_M, BTN_GENDER_F]

    # * Main menu buttons.
    BTN_ACCOUNT = "🎛️ Личный кабинет"
    BTN_DURING_RACE = "🏁 Во время гонки"
    BTN_EVENTS = "🗓️ Мероприятия"
    BTN_MAIN = "🗂️ Главное меню"
    BTN_ADMIN = "⚙️ Администрирование"

    # * Account menu buttons.
    BTN_ACCOUNT_NEW = "🆕 Регистрация"
    BTN_ACCOUNT_INFO = "ℹ️ Мои данные"
    BTN_ACCOUNT_EDIT = "📝 Редактировать"

    # * During race menu buttons.
    BTN_TRANSLATION = "📡 Трансляция геолокации"
    BTN_LEADERBOARD = "🏆 Таблица лидеров"
    BTN_YOUR_STATUS = "📊 Ваши показатели"
    BTN_NEED_HELP = "🆘 Мне нужна помощь"

    # * Events menu buttons.
    UPCOMING_EVENTS = "🚴‍♀️ Предстоящие гонки"

    # * Admin events menu buttons.
    ADMIN_UPCOMING_EVENTS = "🚴‍♂️ Созданные гонки"

    # * Admin menu buttons.
    BTN_MANAGE_RACE = "🏁 Управление гонкой"
    BTN_MANAGE_PAYMENTS = "💵 Управление платежами"
    BTN_MANAGE_EVENTS = "🗓️ Управление мероприятиями"

    # * Main menus.
    MN_MAIN_USER = [BTN_ACCOUNT, BTN_DURING_RACE, BTN_EVENTS]
    MN_MAIN_ADMIN = [
        BTN_ACCOUNT,
        BTN_DURING_RACE,
        BTN_EVENTS,
        BTN_ADMIN,
    ]

    # * Account menus.
    MN_ACCOUNT_NEW = [BTN_ACCOUNT_NEW, BTN_MAIN]
    MN_ACCOUNT_EXIST = [
        BTN_ACCOUNT_INFO,
        BTN_ACCOUNT_EDIT,
        BTN_MAIN,
    ]
    MN_REG = [BTN_CANCEL, BTN_SKIP]
    MN_REG_GENDER = [BTN_GENDER_M, BTN_GENDER_F, BTN_CANCEL]
    MN_REG_CONFIRM = [BTN_CONFIRM, BTN_CANCEL]

    # * During race menu.
    MN_DURING_RACE = [
        BTN_TRANSLATION,
        BTN_LEADERBOARD,
        BTN_YOUR_STATUS,
        BTN_NEED_HELP,
        BTN_MAIN,
    ]

    # * Events menu.
    MN_EVENTS = [UPCOMING_EVENTS, BTN_MAIN]

    # * Admin menu.
    MN_ADMIN = [BTN_MANAGE_RACE, BTN_MANAGE_PAYMENTS, BTN_MANAGE_EVENTS, BTN_MAIN]
    MN_ADMIN_EVENTS = [ADMIN_UPCOMING_EVENTS, BTN_MAIN]
