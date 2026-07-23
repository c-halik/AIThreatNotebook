import config

FILE_FIXTURES = [
    {"filename": "fake_ssns.txt", "label": "Fake SSNs", "content_type": "text/plain"},
    {"filename": "fake_credit_cards.txt", "label": "Fake credit cards", "content_type": "text/plain"},
    {"filename": "fake_api_keys.txt", "label": "Fake API keys", "content_type": "text/plain"},
    {"filename": "fake_proprietary_snippet.py", "label": "Fake proprietary source code", "content_type": "text/x-python"},
]


def load_fixture_bytes(filename: str) -> bytes:
    return (config.TEST_FILES_DIR / filename).read_bytes()
