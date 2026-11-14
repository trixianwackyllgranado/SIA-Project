"""Small JSON-over-HTTPS helper shared by the URL shortener and the SMS tool."""
import json
import urllib.error
import urllib.request

USER_AGENT = "UtilityHub/1.0 (ITL313-18 student project)"


class NetworkError(Exception):
    """The server could not be reached, or its reply was not JSON."""


def request_json(url, method="GET", headers=None, payload=None, timeout=10):
    """Send one request and return (status_code, parsed_json).

    An HTTP error status is returned, not raised, because both APIs put the
    reason for a failure in the JSON body.
    """
    all_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    all_headers.update(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        all_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=all_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except OSError:  # no internet, DNS failure, timeout
        raise NetworkError("no connection") from None
    try:
        return status, json.loads(raw.decode("utf-8"))
    except ValueError:
        raise NetworkError("unreadable reply") from None
