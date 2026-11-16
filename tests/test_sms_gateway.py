import unittest
from unittest import mock

from app import sms_gateway
from app.http_json import NetworkError

SETTINGS = {"TEXTBEE_API_KEY": "test-key", "TEXTBEE_DEVICE_ID": ""}
QUEUED = {"data": {"success": True, "message": "SMS added to queue for processing"}}


def fake_reply(reply, status=200):
    return mock.patch.object(sms_gateway, "request_json", return_value=(status, reply))


class NumberTests(unittest.TestCase):
    def test_accepted_formats(self):
        for text in ["09171234567", "0917 123 4567", "0917-123-4567", "+63 917 123 4567",
                     "639171234567", "(0917) 123.4567"]:
            self.assertEqual(sms_gateway.normalize_ph_mobile(text), "+639171234567", text)

    def test_rejected_formats(self):
        for text in ["", "1234567", "0817 123 4567", "+1 202 555 0123", "0917123456",
                     "091712345678", "0917abc4567"]:
            with self.assertRaises(sms_gateway.SmsError, msg=text):
                sms_gateway.normalize_ph_mobile(text)

    def test_message_limits(self):
        with self.assertRaises(sms_gateway.SmsError):
            sms_gateway.check_message("   ")
        with self.assertRaises(sms_gateway.SmsError):
            sms_gateway.check_message("x" * (sms_gateway.MAX_LENGTH + 1))
        self.assertEqual(sms_gateway.check_message("  hi  "), "hi")


class SendTests(unittest.TestCase):
    def test_success_sends_expected_request(self):
        with fake_reply(QUEUED) as call:
            self.assertEqual(sms_gateway.send_sms(SETTINGS, "0917 123 4567", "Hello"),
                             "+639171234567")
        args, kwargs = call.call_args
        self.assertEqual(args[0], sms_gateway.API_URL)
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["headers"], {"x-api-key": "test-key"})
        self.assertEqual(kwargs["payload"], {"recipients": ["+639171234567"], "message": "Hello"})

    def test_device_id_sent_when_set(self):
        settings = dict(SETTINGS, TEXTBEE_DEVICE_ID="abc123")
        with fake_reply(QUEUED) as call:
            sms_gateway.send_sms(settings, "09171234567", "Hello")
        self.assertEqual(call.call_args.kwargs["payload"]["deviceId"], "abc123")

    def test_missing_key_never_calls_api(self):
        with fake_reply(QUEUED) as call:
            with self.assertRaisesRegex(sms_gateway.SmsError, "TEXTBEE_API_KEY"):
                sms_gateway.send_sms({}, "09171234567", "Hello")
        call.assert_not_called()

    def test_error_statuses(self):
        cases = [(401, {}, "API key"), (404, {}, "device"), (429, {}, "limit"),
                 (400, {"success": False, "error": "No enabled device"}, "No enabled device"),
                 (500, "not a dict", "HTTP 500"),
                 (200, {"data": {"success": False}}, "HTTP 200")]
        for status, reply, expected in cases:
            with fake_reply(reply, status):
                with self.assertRaisesRegex(sms_gateway.SmsError, expected):
                    sms_gateway.send_sms(SETTINGS, "09171234567", "Hello")

    def test_no_internet(self):
        with mock.patch.object(sms_gateway, "request_json", side_effect=NetworkError("x")):
            with self.assertRaisesRegex(sms_gateway.SmsError, "internet"):
                sms_gateway.send_sms(SETTINGS, "09171234567", "Hello")


if __name__ == "__main__":
    unittest.main()
