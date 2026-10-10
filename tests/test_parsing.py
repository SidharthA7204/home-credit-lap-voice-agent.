import pytest

from app.extractor import amounts_in, normalize, tenure_in


@pytest.mark.parametrize("text,expected", [
    ("fifty lakh", [50]), ("1.2 crore", [120]), ("seventy-five lakhs", [75]),
    ("one crore", [100]), ("1,00,00,000", [100]), ("90 lakh", [90]),
])
def test_amounts(text, expected):
    assert amounts_in(normalize(text)) == expected


@pytest.mark.parametrize("text,expected", [
    ("ten years", 10), ("fifteen years and six months", 15.5), ("two years", 2), ("24 months", 2),
    ("a 10 years old house", None),
])
def test_tenure(text, expected):
    assert tenure_in(normalize(text)) == expected
