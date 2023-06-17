from django import forms


class NewRaceForm(forms.Form):
    name = forms.CharField(label="Название гонки")
    start = forms.DateTimeField(
        label="Дата и время начала",
        input_formats=["%d.%m.%Y %H:%M"],
        help_text="Указывается в UTC. Формат: ДД.ММ.ГГГГ ЧЧ:ММ",
    )
    location = forms.CharField(
        label="Координаты старта",
        help_text="Например: 55.7558, 37.6173",
    )
    code = forms.CharField(
        label="Код гонки",
        help_text="Например: TDS, TZAR",
    )
    categories = forms.CharField(
        label="Категории", help_text="Например: М: ЦК, Ж: Шоссе"
    )
    distance = forms.FloatField(label="Дистанция (км)")
    price = forms.IntegerField(label="Стоимость")
    registration_open = forms.BooleanField(label="Открыть регистрацию", required=False)
