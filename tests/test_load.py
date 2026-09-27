from ingest.catalog import Scheme
from ingest.load import markdown_from_fields

SCHEME = Scheme(
    scheme_id="hdfc-elss",
    scheme_name="HDFC ELSS Tax Saver Fund",
    category="ELSS",
    source_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
)


def test_markdown_keeps_labels_with_numbers_and_drops_returns():
    text = markdown_from_fields(
        SCHEME,
        {
            "expense_ratio": 1.21,
            "exit_load": "Nil",
            "min_sip_investment": 500,
            "lock_in": {"years": 3, "months": 0, "days": 0},
            "return_stats": [{"risk": "Very High", "return1y": 12.5}],
            "benchmark_name": "NIFTY 500 Total Return Index",
            "peerComparison": [{"scheme_name": "Other Fund", "expense_ratio": 0.5}],
            "stats": [{"title": "Fund Returns", "stat_1y": 9.1}],
        },
    )
    assert text.startswith("# HDFC ELSS Tax Saver Fund\n")
    assert "Expense ratio: 1.21%." in text
    assert "Exit load: Nil." in text
    assert "Minimum SIP: 500." in text
    assert "Lock-in: 3 years." in text
    assert "Riskometer: Very High." in text
    assert "return1y" not in text
    assert "Other Fund" not in text
    assert "Fund Returns" not in text
