"""Synthetic case fixtures.

Every case here is invented. The generator covers the situations that decide
whether a verification pipeline is useful: the boring matches it should clear
without help, the harmless variations that must not be treated as mismatches,
and the cases that genuinely need a person to look.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCENARIOS: tuple[str, ...] = (
    "clean_video_match",
    "transliteration_variant",
    "name_order_swapped",
    "middle_name_missing",
    "dob_day_month_transposed",
    "document_number_ocr_confusion",
    "second_person_in_frame",
    "different_person_in_video",
    "data_only_clean",
    "data_only_name_mismatch",
    "video_expected_but_absent",
)


def _frames(identity: str, count: int = 10, *, intruder_from: int | None = None, intruder: str = "id-999") -> list[dict[str, Any]]:
    frames = []
    for i in range(count):
        faces = [identity]
        if intruder_from is not None and i >= intruder_from:
            faces.append(intruder)
        frames.append(
            {
                "uri": f"s3://synthetic/{identity}/frame-{i:02d}.jpg",
                "identity_seed": identity,
                "capture": f"frame-{i:02d}",
                "faces": faces,
            }
        )
    return frames


def _video_case(
    reference: str,
    *,
    declared_name: str,
    document_name: str,
    declared_dob: str,
    document_dob: str,
    declared_number: str,
    document_number: str,
    selfie_identity: str,
    document_identity: str,
    video_identity: str | None,
    intruder_from: int | None = None,
) -> dict[str, Any]:
    media: dict[str, Any] = {
        "selfie": {"uri": f"s3://synthetic/{reference}/selfie.jpg", "identity_seed": selfie_identity, "capture": "selfie"},
        "documentPortrait": {
            "uri": f"s3://synthetic/{reference}/portrait.jpg",
            "identity_seed": document_identity,
            "capture": "portrait",
        },
    }
    if video_identity is not None:
        media["video"] = {
            "uri": f"s3://synthetic/{reference}/video.mp4",
            "durationSeconds": 18.0,
            "frames": _frames(video_identity, intruder_from=intruder_from),
        }
    return {
        "provider": "video_capable",
        "reference": reference,
        "declared": {
            "fullName": declared_name,
            "dateOfBirth": declared_dob,
            "nationality": "BGD",
            "documentNumber": declared_number,
        },
        "document": {
            "type": "passport",
            "fullName": document_name,
            "dateOfBirth": document_dob,
            "nationality": "BGD",
            "number": document_number,
        },
        "media": media,
    }


def _data_only_case(applicant_id: str, *, declared_name: str, document_name: str, identity: str) -> dict[str, Any]:
    return {
        "provider": "data_only",
        "applicantId": applicant_id,
        "info": {
            "fullName": declared_name,
            "dob": "17/04/1993",
            "country": "MYS",
            "idDocNumber": "A1234567",
        },
        "idDoc": {
            "docType": "ID_CARD",
            "fullName": document_name,
            "dob": "1993-04-17",
            "country": "MYS",
            "number": "A1234567",
        },
        "images": {
            "selfie": {"uri": f"s3://synthetic/{applicant_id}/selfie.jpg", "identity_seed": identity, "capture": "selfie"},
            "docPortrait": {"uri": f"s3://synthetic/{applicant_id}/portrait.jpg", "identity_seed": identity, "capture": "portrait"},
        },
    }


def generate() -> list[dict[str, Any]]:
    """One payload per scenario, deterministic and safe to commit."""
    cases: list[dict[str, Any]] = []

    cases.append(
        _video_case(
            "clean_video_match",
            declared_name="Arif Rahman Chowdhury",
            document_name="Arif Rahman Chowdhury",
            declared_dob="1993-04-17",
            document_dob="1993-04-17",
            declared_number="BP7741820",
            document_number="BP7741820",
            selfie_identity="id-101",
            document_identity="id-101",
            video_identity="id-101",
        )
    )
    cases.append(
        _video_case(
            "transliteration_variant",
            declared_name="Md. Kamal Hossain",
            document_name="Mohammad Kamal Hosain",
            declared_dob="1990-11-02",
            document_dob="1990-11-02",
            declared_number="BP5520114",
            document_number="BP5520114",
            selfie_identity="id-102",
            document_identity="id-102",
            video_identity="id-102",
        )
    )
    cases.append(
        _video_case(
            "name_order_swapped",
            declared_name="Chowdhury Nusrat Jahan",
            document_name="Nusrat Jahan Chowdhury",
            declared_dob="1995-02-09",
            document_dob="1995-02-09",
            declared_number="BP3390277",
            document_number="BP3390277",
            selfie_identity="id-103",
            document_identity="id-103",
            video_identity="id-103",
        )
    )
    cases.append(
        _video_case(
            "middle_name_missing",
            declared_name="Sadia Islam",
            document_name="Sadia Akter Islam",
            declared_dob="1992-06-30",
            document_dob="1992-06-30",
            declared_number="BP8811902",
            document_number="BP8811902",
            selfie_identity="id-104",
            document_identity="id-104",
            video_identity="id-104",
        )
    )
    cases.append(
        _video_case(
            "dob_day_month_transposed",
            declared_name="Tanvir Ahmed",
            document_name="Tanvir Ahmed",
            declared_dob="1991-05-08",
            document_dob="1991-08-05",
            declared_number="BP2245901",
            document_number="BP2245901",
            selfie_identity="id-105",
            document_identity="id-105",
            video_identity="id-105",
        )
    )
    cases.append(
        _video_case(
            "document_number_ocr_confusion",
            declared_name="Farhana Yeasmin",
            document_name="Farhana Yeasmin",
            declared_dob="1994-01-21",
            document_dob="1994-01-21",
            declared_number="BP0O12345",
            document_number="BP0012345",
            selfie_identity="id-106",
            document_identity="id-106",
            video_identity="id-106",
        )
    )
    cases.append(
        _video_case(
            "second_person_in_frame",
            declared_name="Rakib Hasan",
            document_name="Rakib Hasan",
            declared_dob="1996-09-14",
            document_dob="1996-09-14",
            declared_number="BP6678230",
            document_number="BP6678230",
            selfie_identity="id-107",
            document_identity="id-107",
            video_identity="id-107",
            intruder_from=4,
        )
    )
    cases.append(
        _video_case(
            "different_person_in_video",
            declared_name="Imran Kabir",
            document_name="Imran Kabir",
            declared_dob="1989-12-05",
            document_dob="1989-12-05",
            declared_number="BP4432118",
            document_number="BP4432118",
            selfie_identity="id-108",
            document_identity="id-108",
            video_identity="id-777",
        )
    )
    cases.append(
        _video_case(
            "video_expected_but_absent",
            declared_name="Priya Das",
            document_name="Priya Das",
            declared_dob="1997-03-11",
            document_dob="1997-03-11",
            declared_number="BP9903471",
            document_number="BP9903471",
            selfie_identity="id-109",
            document_identity="id-109",
            video_identity=None,
        )
    )
    cases.append(
        _data_only_case(
            "data_only_clean",
            declared_name="Nurul Aina Binti Zulkifli",
            document_name="Nurul Aina Zulkifli",
            identity="id-201",
        )
    )
    cases.append(
        _data_only_case(
            "data_only_name_mismatch",
            declared_name="Wei Ling Tan",
            document_name="Siti Aminah Rahman",
            identity="id-202",
        )
    )
    return cases


def write(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(generate(), indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write synthetic KYC case fixtures.")
    parser.add_argument("--out", default="data/synthetic/cases.json", help="output path")
    args = parser.parse_args(argv)
    written = write(Path(args.out))
    print(f"wrote {len(generate())} synthetic cases to {written}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
