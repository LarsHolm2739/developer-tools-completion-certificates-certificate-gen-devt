from src.certificate_service import BuildEvent, CertificateService


class FakeClient:
    def __init__(self):
        self.calls = []

    def generate_certificate(self, event):
        self.calls.append(("pdf", event))
        return "pdf-123"

    def send_certificate_batch(self, event, pdf_reference):
        self.calls.append(("email", event, pdf_reference))
        return "message-456"


def test_published_release_generates_before_batch_email():
    client = FakeClient()
    event = BuildEvent("Lin", "compiler-lab", "v2.0.0", "lin@example.com")

    result = CertificateService(client).complete_release(event)

    assert result.pdf_reference == "pdf-123"
    assert result.message_id == "message-456"
    assert [call[0] for call in client.calls] == ["pdf", "email"]
    assert client.calls[1][2] == "pdf-123"


def test_unpublished_release_stays_out_of_the_api():
    client = FakeClient()
    event = BuildEvent("Lin", "compiler-lab", "v2.0.0", "lin@example.com", published=False)

    try:
        CertificateService(client).complete_release(event)
    except ValueError as error:
        assert str(error) == "release is not published"
    else:
        raise AssertionError("an unpublished release must be rejected")
    assert client.calls == []
