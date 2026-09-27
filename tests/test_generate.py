from app.generate import generate

ELSS = {
    "document": (
        "Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth\n"
        "Expense ratio: 1.21%. Base expense ratio: 0.97%."
    ),
    "scheme_id": "hdfc-elss",
    "scheme_name": "HDFC ELSS Tax Saver Fund",
    "section": "Expense ratio",
    "source_url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
}


def test_answer_includes_the_fact_and_the_scheme_description():
    text = generate("What is the expense ratio of HDFC ELSS Tax Saver?", [ELSS])
    assert "The expense ratio of HDFC ELSS Tax Saver Fund is 1.21%" in text
    assert "base expense ratio is 0.97%" in text
    assert "capital appreciation" in text
    assert "you should" not in text.lower()


def test_sip_amount_is_not_followed_by_a_double_period():
    text = generate(
        "What is the minimum SIP for HDFC Small Cap Fund?",
        [
            {
                "document": "Source: https://example.com\nMinimum SIP: 100. Minimum lump-sum investment: 100.",
                "scheme_id": "hdfc-small-cap",
                "scheme_name": "HDFC Small Cap Fund",
                "section": "Minimum SIP",
                "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            }
        ],
    )
    assert "is 100." in text
    assert "100.." not in text
    assert "100.," not in text
