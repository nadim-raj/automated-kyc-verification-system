"""Provider adapters.

Two shapes of provider exist in this reference: one that returns a recorded
video alongside the documents, and one that returns documents and stills only.
Both are translated into the same domain objects here, so no downstream code
has to care which provider a case came from — and adding a third provider means
writing one adapter rather than touching the pipeline.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

from .domain import (
    DocumentExtract,
    IdentityClaim,
    ImageRef,
    MediaBundle,
    ProviderKind,
    VerificationCase,
    VideoRef,
)

_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d-%b-%Y", "%Y/%m/%d")


def parse_date(value: Any) -> date | None:
    """Parse the date formats providers actually send."""
    if isinstance(value, date):
        return value
    if not value or not isinstance(value, str):
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _image(payload: Mapping[str, Any] | None) -> ImageRef | None:
    if not payload:
        return None
    data = dict(payload)
    uri = str(data.pop("uri", ""))
    return ImageRef(uri=uri, payload=data)


def from_video_capable(payload: Mapping[str, Any]) -> VerificationCase:
    """Adapt a provider that returns documents, stills, and a recorded video."""
    declared = payload.get("declared", {})
    document = payload.get("document", {})
    media = payload.get("media", {})
    video_payload = media.get("video")

    video = None
    if video_payload:
        video = VideoRef(
            uri=str(video_payload.get("uri", "")),
            duration_s=float(video_payload.get("durationSeconds", 0.0)),
            frames=tuple(f for f in (_image(frame) for frame in video_payload.get("frames", [])) if f),
        )

    return VerificationCase(
        case_id=str(payload.get("reference", "")),
        provider=ProviderKind.VIDEO_CAPABLE,
        claim=IdentityClaim(
            full_name=str(declared.get("fullName", "")),
            date_of_birth=parse_date(declared.get("dateOfBirth")),
            nationality=declared.get("nationality"),
            document_number=declared.get("documentNumber"),
        ),
        document=DocumentExtract(
            full_name=str(document.get("fullName", "")),
            date_of_birth=parse_date(document.get("dateOfBirth")),
            nationality=document.get("nationality"),
            document_number=document.get("number"),
            document_type=document.get("type"),
        ),
        media=MediaBundle(
            selfie=_image(media.get("selfie")),
            document_portrait=_image(media.get("documentPortrait")),
            video=video,
        ),
    )


def from_data_only(payload: Mapping[str, Any]) -> VerificationCase:
    """Adapt a provider that returns documents and stills but never video."""
    info = payload.get("info", {})
    doc = payload.get("idDoc", {})
    images = payload.get("images", {})

    return VerificationCase(
        case_id=str(payload.get("applicantId", "")),
        provider=ProviderKind.DATA_ONLY,
        claim=IdentityClaim(
            full_name=str(info.get("fullName", "")),
            date_of_birth=parse_date(info.get("dob")),
            nationality=info.get("country"),
            document_number=info.get("idDocNumber"),
        ),
        document=DocumentExtract(
            full_name=str(doc.get("fullName", "")),
            date_of_birth=parse_date(doc.get("dob")),
            nationality=doc.get("country"),
            document_number=doc.get("number"),
            document_type=doc.get("docType"),
        ),
        media=MediaBundle(
            selfie=_image(images.get("selfie")),
            document_portrait=_image(images.get("docPortrait")),
            video=None,
        ),
    )


ADAPTERS = {
    ProviderKind.VIDEO_CAPABLE.value: from_video_capable,
    ProviderKind.DATA_ONLY.value: from_data_only,
}


def load_case(payload: Mapping[str, Any]) -> VerificationCase:
    """Dispatch to the right adapter using the payload's ``provider`` field."""
    provider = str(payload.get("provider", ""))
    try:
        adapter = ADAPTERS[provider]
    except KeyError:
        raise ValueError(f"unknown provider: {provider!r}") from None
    return adapter(payload)
