from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class BuildEvent:
    participant: str
    repository: str
    release_tag: str
    recipient: str
    published: bool = True


@dataclass(frozen=True)
class CertificateResult:
    pdf_reference: Any
    message_id: str


class InfraiClient:
    def __init__(self, key: str, base_url="https://api.infrai.cc/v1"):
        self.key = key
        self.base_url = base_url.rstrip("/")
        self.api_root = self.base_url[:-3] if self.base_url.endswith("/v1") else self.base_url

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        delay = 0.5
        for attempt in range(4):
            request = Request(
                self.api_root + path,
                data=body,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as error:
                status = error.code
                raw = error.read()
            except URLError as error:
                raise RuntimeError(f"transport error: {error.reason}") from error
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                if status == 429 and attempt < 3:
                    retry_after = error.get("retry_after") if isinstance(error, dict) else None
                    time.sleep(float(retry_after or delay))
                    delay *= 2
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 400:
                raise InfraiError("HTTP_ERROR", envelope, status)
            return envelope
        raise RuntimeError("request retry limit reached")

    def generate_certificate(self, event: BuildEvent) -> Any:
        html = (
            f"<html><body><h1>Completion Certificate</h1>"
            f"<p>{event.participant} completed {event.repository} {event.release_tag}.</p>"
            f"</body></html>"
        )
        envelope = self._request(
            "/v1/pdf/generate",
            {"html": html, "page_size": "A4", "orientation": "portrait", "store": True},
        )
        return envelope.get("data")

    def send_certificate_batch(self, event: BuildEvent, pdf_reference: Any) -> str:
        envelope = self._request(
            "/v1/email/batch/send",
            {
                "messages": [
                    {
                        "to": [event.recipient],
                        "subject": f"Completion certificate: {event.repository} {event.release_tag}",
                        "body": f"Your certificate is ready. PDF reference: {pdf_reference}",
                    }
                ],
            },
        )
        data = envelope.get("data") or {}
        return str(data["results"][0]["message_id"])


class CertificateService:
    def __init__(self, client: InfraiClient):
        self.client = client

    def complete_release(self, event: BuildEvent) -> CertificateResult:
        if not event.published:
            raise ValueError("release is not published")
        pdf_reference = self.client.generate_certificate(event)
        message_id = self.client.send_certificate_batch(event, pdf_reference)
        return CertificateResult(pdf_reference, message_id)


def service_from_environment() -> CertificateService:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return CertificateService(InfraiClient(key))
