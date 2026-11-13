from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.internal.models import Audiobook
from app.internal.prowlarr.prowlarr import query_variants
from tests.constants import ASIN
from tests.http import as_list, json_object
from tests.mock_services import MockServer


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Test Book", ["Test Book"]),
        (
            "Azarinth Healer, Book Six",
            ["Azarinth Healer, Book Six", "Azarinth Healer, Book 6"],
        ),
        (
            "Azarinth Healer 6",
            ["Azarinth Healer 6", "Azarinth Healer Six"],
        ),
        ("Cradle, Book Seventeen", ["Cradle, Book Seventeen", "Cradle, Book 17"]),
        ("Mark of the Fool 4.5", ["Mark of the Fool 4.5"]),
        ("Someone Like You", ["Someone Like You"]),
        ("1984", ["1984"]),
    ],
)
def test_query_variants(title: str, expected: list[str]) -> None:
    assert query_variants(title) == expected


def test_sources_search_every_number_spelling(
    admin_client: TestClient, prowlarr: MockServer, db: Session
) -> None:
    book = db.get(Audiobook, ASIN)
    assert book is not None
    book.title = "Test Book Six"
    db.add(book)
    db.commit()

    response = admin_client.get(f"/api/requests/{ASIN}/sources")
    assert response.status_code == 200, response.text

    queries = {
        request["query"]["query"]
        for request in prowlarr.requests_to("/prowlarr/api/v1/search")
        if request["method"] == "GET"
    }
    assert queries == {"Test Book Six", "Test Book 6"}
    # both searches return the same release, which must only be listed once
    assert len(as_list(json_object(response)["sources"])) == 1
