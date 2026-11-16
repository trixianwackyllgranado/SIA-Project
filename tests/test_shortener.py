import unittest
from unittest import mock

from app import shortener
from app.http_json import NetworkError


def fake_reply(reply, status=200):
    return mock.patch.object(shortener, "request_json", return_value=(status, reply))


class CleanUrlTests(unittest.TestCase):
    def test_adds_https_when_missing(self):
        self.assertEqual(shortener.clean_url(" www.python.org "), "https://www.python.org")

    def test_keeps_valid_links(self):
        url = "http://example.com/a?b=1&c=two#top"
        self.assertEqual(shortener.clean_url(url), url)

    def test_rejects_bad_links(self):
        for bad in ["", "   ", "ftp://example.com", "javascript:alert(1)", "https://localhost",
                    "has space.com", "https://example.com:99999", "https://" + "a" * 2000 + ".com"]:
            with self.assertRaises(shortener.ShortenerError, msg=bad):
                shortener.clean_url(bad)


class ShortenTests(unittest.TestCase):
    def test_success(self):
        with fake_reply({"shorturl": "https://is.gd/abc123"}) as call:
            self.assertEqual(shortener.shorten("example.com/page"),
                             ("https://example.com/page", "https://is.gd/abc123"))
        sent_url = call.call_args[0][0]
        self.assertTrue(sent_url.startswith("https://is.gd/create.php?format=json&url="))
        self.assertIn("https%3A%2F%2Fexample.com%2Fpage", sent_url)

    def test_rate_limit_message(self):
        with fake_reply({"errorcode": 3, "errormessage": "Rate limit"}):
            with self.assertRaisesRegex(shortener.ShortenerError, "Wait a minute"):
                shortener.shorten("https://example.com")

    def test_api_error_message_passed_on(self):
        with fake_reply({"errorcode": 1, "errormessage": "Blacklisted domain"}):
            with self.assertRaisesRegex(shortener.ShortenerError, "Blacklisted domain"):
                shortener.shorten("https://example.com")

    def test_unexpected_reply_is_not_trusted(self):
        for reply in [{"shorturl": "https://evil.example/x"}, [], {}]:
            with fake_reply(reply):
                with self.assertRaises(shortener.ShortenerError):
                    shortener.shorten("https://example.com")

    def test_no_internet(self):
        with mock.patch.object(shortener, "request_json", side_effect=NetworkError("x")):
            with self.assertRaisesRegex(shortener.ShortenerError, "internet"):
                shortener.shorten("https://example.com")

    def test_invalid_link_never_calls_api(self):
        with fake_reply({}) as call:
            with self.assertRaises(shortener.ShortenerError):
                shortener.shorten("ftp://example.com")
        call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
