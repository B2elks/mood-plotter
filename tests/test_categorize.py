from categorize import categorize


def test_empty_returns_neutral():
    assert categorize("") == "neutral"
    assert categorize("   ") == "neutral"


def test_happy_keywords():
    assert categorize("Jag är super glad idag!") == "happy"
    assert categorize("Det är härligt") == "happy"
    assert categorize("Bra dag") == "happy"


def test_tired_keywords():
    assert categorize("Jag är trött och sliten") == "tired"
    assert categorize("Utmattad") == "tired"


def test_stressed_keywords():
    assert categorize("Helt stressad just nu") == "stressed"
    assert categorize("Det är jobbigt och bråttom") == "stressed"


def test_sad_keywords():
    assert categorize("Jag är så ledsen") == "sad"
    assert categorize("Lite deppig och dålig") == "sad"


def test_neutral_default():
    assert categorize("Vet inte riktigt") == "neutral"
    assert categorize("Tja det går") == "neutral"


def test_negative_keywords_win_over_positive():
    # If both happy and tired keywords are present, tired wins (closer to need)
    assert categorize("Jag är glad men trött") == "tired"


def test_case_and_accents_insensitive():
    assert categorize("TROTT") == "tired"
    assert categorize("Trött") == "tired"
    assert categorize("Ledsen") == "sad"
