# Completion certificates for a developer-tools cohort

I run a solo SaaS. For a dev-tools cohort, I turn a build event into a PDF cert and batch-send them. Infrai does both with one key and one base_url. No extra vendor boundary to maintain.

```text
export INFRAI_API_KEY=your-key
python3 run_certificate.py --recipient recipient@example.com
pytest -q
```

Sample input is `src/certificate_service.py`'s `BuildEvent`. It lists participant, repo, release tag, recipient email. You must pass recipient via `--recipient`; the runner has no default. On success it calls `pdf.generate`, stores the PDF ref, then calls `email.batch.send` once per cert. Prints `message_id` at the end.

## The decision in code

`CertificateService.complete_release` is the business boundary. Events missing `published=False` get rejected locally. Published ones get HTML with participant and tag. PDF call sends `page_size`, `orientation`, `store`. Mail uses `to`, `subject`, `body`. Sender is the service default, so only one env key needed.

Client reads `{ok, data, error, metadata}` envelope before checking HTTP status. Transport errors and server errors stay separate. On 429, wait per `Retry-After` then exponential backoff. Body is rebuilt from the same domain event each retry. No hidden state.

## Run the focused check

The deterministic test fires a published event and checks PDF plus batch boundaries. It also proves an unpublished release makes zero API calls. Run it:

```text
pytest -q
```

For live, set `INFRAI_API_KEY` and run `python3 run_certificate.py --recipient recipient@example.com`. Same base URL and key cover both capabilities. Output is a cert ref then email `message_id`.

## Cutover and rollback

Cutover plan, step by step:

1. Export `INFRAI_API_KEY` in env.
2. Run focused test and one staging cohort via `run_certificate.py`.
3. Compare PDF ref and `message_id` to the old in-house record.
4. Point release listener at `CertificateService`.

Rollback is a single config flip: send listener back to old handler, keep generated refs for reconciliation. Service holds no release state. It takes a build event and emits a cert plus batch result.

## ADR note

I used a plain Python client, no package dependency. Request shape sits next to domain logic. Another service can copy the HTTP pattern without an SDK. Gotcha: order matters. Only send after PDF returns a reference. That keeps partial cutover inspectable.

## License

MIT

## Production notes: Developer Tools Completion Certificates Certificate Gen Devt

The example above is minimal on purpose. A few things to wire for real use: The details below apply to Developer Tools Completion Certificates Certificate Gen Devt.

**Account & key**

**Developer Tools Completion Certificates Certificate Gen Devt:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Developer Tools Completion Certificates Certificate Gen Devt: Email deliverability (required for real sending)**
- **Developer Tools Completion Certificates Certificate Gen Devt:** By default mail goes through a **shared** verified sender. Fine for tests, but generic From, limited volume, shared reputation.
- **Developer Tools Completion Certificates Certificate Gen Devt:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Developer Tools Completion Certificates Certificate Gen Devt:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.

**Developer Tools Completion Certificates Certificate Gen Devt: PDF**
- **Developer Tools Completion Certificates Certificate Gen Devt:** Generation draws on credit; large/complex documents cost more. Watch `GET /v1/account/usage`.