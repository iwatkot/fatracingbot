import os
import hashlib
import hmac

import globals as g

logger = g.Logger(__name__)

AUTH_BOT_TOKEN = os.getenv("AUTH_BOT_TOKEN")


def validate_login(query: dict) -> bool:
    sorted_keys = sorted(query.keys())
    received_hash = query.get("hash")
    if not received_hash:
        return False

    logger.debug(f"Receiving attempt to login with telegram id {query.get('id')}.")

    data_check_string = "\n".join(
        [f"{key}={query[key]}" for key in sorted_keys if key != "hash"]
    )

    secret_key = hashlib.sha256(AUTH_BOT_TOKEN.encode()).digest()
    signature = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    res = signature == received_hash

    logger.debug(
        f"Result of login validation for telegram id {query.get('id')}: {res}."
    )

    return res
