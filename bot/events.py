from re import escape

from aiogram.dispatcher.filters import Text

from main import bot, dp
import database as db
import globals as g
from templates import Messages, Buttons
import utility

logger = g.Logger(__name__)
