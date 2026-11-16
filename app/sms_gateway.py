"""SMS sending through the TextBee API.

TextBee turns an Android phone into an SMS gateway: the API queues the
message and the phone sends it using its own SIM.
API reference: https://textbee.dev/docs/sending-sms/sending-sms
"""
import re

from app.http_json import NetworkError, request_json

API_URL = "https://api.textbee.dev/api/v1/gateway/send-sms"
MAX_LENGTH = 320  # two standard SMS segments

_SEPARATORS = re.compile(r"[\s\-().]")
NUMBER_HINT = "Enter a PH mobile number like 0917 123 4567 or +63 917 123 4567."


class SmsError(Exception):
    """A message that is safe to show to the user."""


def normalize_ph_mobile(text):
    """Return the number as +639XXXXXXXXX, or raise SmsError."""
    digits = _SEPARATORS.sub("", text or "")
    if re.fullmatch(r"09\d{9}", digits):
        return "+63" + digits[1:]
    if re.fullmatch(r"639\d{9}", digits):
        return "+" + digits
    if re.fullmatch(r"\+639\d{9}", digits):
        return digits
    raise SmsError(NUMBER_HINT)


def check_message(text):
    message = (text or "").strip()
    if not message:
        raise SmsError("Type a message first.")
    if len(message) > MAX_LENGTH:
        raise SmsError(f"Message is too long ({len(message)}/{MAX_LENGTH} characters).")
    return message


def send_sms(settings, number, message):
    """Queue one SMS. Returns the normalized number. Raises SmsError on any failure."""
    recipient = normalize_ph_mobile(number)
    message = check_message(message)
    api_key = settings.get("TEXTBEE_API_KEY")
    if not api_key:
        raise SmsError("SMS is not set up. Add TEXTBEE_API_KEY to the .env file.")

    payload = {"recipients": [recipient], "message": message}
    if settings.get("TEXTBEE_DEVICE_ID"):
        payload["deviceId"] = settings["TEXTBEE_DEVICE_ID"]
    try:
        status, reply = request_json(API_URL, method="POST", headers={"x-api-key": api_key},
                                     payload=payload)
    except NetworkError:
        raise SmsError("Couldn't reach TextBee. Check your internet connection.") from None

    reply = reply if isinstance(reply, dict) else {}
    result = reply.get("data")
    if status == 200 and isinstance(result, dict) and result.get("success"):
        return recipient
    if status == 401:
        raise SmsError("TextBee rejected the API key. Check TEXTBEE_API_KEY in .env.")
    if status == 404:
        raise SmsError("TextBee can't find that device. Check TEXTBEE_DEVICE_ID in .env.")
    if status == 429:
        raise SmsError("Your TextBee plan limit is used up for now.")
    reason = reply.get("error") or reply.get("message")
    if isinstance(reason, str) and reason:
        raise SmsError(f"TextBee couldn't send the message: {reason[:200]}")
    raise SmsError(f"TextBee couldn't send the message (HTTP {status}).")
