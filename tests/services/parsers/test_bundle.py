from datetime import datetime
from typing import Any, Dict, List

import pytest
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.patient import Patient

from app.services.parsers.bundle import BundleParser


@pytest.fixture
def mock_bundle_without_entries() -> Dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [{"relation": "self", "url": "http://example.org"}],
    }


@pytest.fixture
def bundle_without_entries(mock_bundle_without_entries: Dict[str, Any]) -> Bundle:
    return Bundle.model_validate(mock_bundle_without_entries)


def test_get_latest_time_stamp_shoud_succeed(regular_bundle: Bundle, datetime_now: str) -> None:
    actual = BundleParser.get_latest_timestamp(regular_bundle)

    assert datetime_now == actual


def test_get_latest_time_stamp_should_return_none_whith_bundle_without_entries(
    bundle_without_entries: Bundle,
) -> None:
    actual = BundleParser.get_latest_timestamp(bundle_without_entries)

    assert actual is None


def test_get_timestamp_should_succeed(regular_bundle: Bundle, datetime_now: str) -> None:
    # typechecker happy
    assert regular_bundle.entry
    assert len(regular_bundle.entry) > 0

    entry = regular_bundle.entry[0]

    actual = BundleParser.get_timestamps(entry)

    assert datetime.fromisoformat(datetime_now) == actual


def test_get_timestamp_should_return_none_with_entry_without_resource() -> None:
    entry = BundleEntry.model_construct()

    actual = BundleParser.get_timestamps(entry)

    assert actual is None


def test_get_patients_should_succeed(regular_bundle: Bundle, patient: Patient) -> None:
    expected = [patient]

    actual = BundleParser.get_patients(regular_bundle)

    assert expected == actual


def test_get_patients_should_return_empty_list_when_no_entries_in_bundle(
    bundle_without_entries: Bundle,
) -> None:
    expected: List[Patient] = []

    actual = BundleParser.get_patients(bundle_without_entries)

    assert expected == actual
