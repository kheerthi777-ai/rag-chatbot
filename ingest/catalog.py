"""The only schemes this prototype may index or cite."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scheme:
    scheme_id: str
    scheme_name: str
    category: str
    source_url: str


SCHEMES: tuple[Scheme, ...] = (
    Scheme(
        scheme_id="hdfc-large-cap",
        scheme_name="HDFC Large Cap Fund",
        category="Large Cap",
        source_url="https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    ),
    Scheme(
        scheme_id="hdfc-flexi-cap",
        scheme_name="HDFC Flexi Cap Fund",
        category="Flexi Cap",
        source_url="https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    ),
    Scheme(
        scheme_id="hdfc-elss",
        scheme_name="HDFC ELSS Tax Saver Fund",
        category="ELSS",
        source_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    ),
    Scheme(
        scheme_id="hdfc-small-cap",
        scheme_name="HDFC Small Cap Fund",
        category="Small Cap",
        source_url="https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    ),
    Scheme(
        scheme_id="hdfc-balanced-advantage",
        scheme_name="HDFC Balanced Advantage Fund",
        category="Hybrid",
        source_url="https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
    ),
)


def url_for(scheme_id: str) -> str:
    for scheme in SCHEMES:
        if scheme.scheme_id == scheme_id:
            return scheme.source_url
    raise KeyError(scheme_id)


def is_catalog_url(url: str) -> bool:
    return any(scheme.source_url == url for scheme in SCHEMES)
