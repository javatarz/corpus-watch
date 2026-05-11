# CAS PDF test fixtures

Place a sanitised CAS PDF here to enable integration tests:

- `cams_sample.pdf` — CAMS CAS statement with PAN and personal data redacted
- `kfintech_sample.pdf` — KFintech CAS statement (optional)

These files are `.gitignore`d. To generate one:
1. Request a CAS from https://new.camsonline.com or https://mfs.kfintech.com
2. Open the PDF, redact PAN and name fields, save as `cams_sample.pdf`
3. Note the password (original PAN) in a local `.env.test` — never commit it

CI skips these tests. Run locally with:
```
uv run pytest tests/integration/ -m integration
```
