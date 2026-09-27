from app.intent import classify


def test_intent_table():
    cases = [
        ("What is the expense ratio of HDFC Large Cap Fund Direct Growth?", "factual", "hdfc-large-cap"),
        ("What is the lock-in period for HDFC ELSS Tax Saver?", "factual", "hdfc-elss"),
        ("What is the minimum SIP for HDFC Small Cap Fund?", "factual", "hdfc-small-cap"),
        ("Exit load of the flexi cap fund?", "factual", "hdfc-flexi-cap"),
        ("Benchmark of HDFC Balanced Advantage?", "factual", "hdfc-balanced-advantage"),
        ("Should I buy HDFC Small Cap?", "advice", "hdfc-small-cap"),
        ("Which of these has the highest 3-year return?", "returns", None),
        ("Should I buy the one with the best return?", "advice", None),
        ("Expense ratio of HDFC Nifty 200 Momentum?", "factual", None),
        ("My PAN is ABCDE1234F", "pii", None),
    ]
    for question, kind, scheme_id in cases:
        intent = classify(question)
        assert intent.kind == kind
        assert intent.scheme_id == scheme_id
        assert question not in (intent.kind, intent.scheme_id or "")
        assert "ABCDE1234F" not in repr(intent) or kind != "pii"


def test_equity_fund_is_flexi_and_two_names_do_not_filter():
    assert classify("Exit load of HDFC Equity Fund?").scheme_id == "hdfc-flexi-cap"
    both = classify("Compare large cap and small cap exit load?")
    assert both.scheme_id is None
