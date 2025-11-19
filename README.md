# Dual Access Control (Flask)

This is a minimal, runnable prototype implementing the project summary:
- CP-ABE-style attribute policies (simulated) for access control
- Dual verification: challenge endpoint gates downloads to mitigate EDoS
- AES-GCM for at-rest encryption
- SQLite persistence for users, files, keys, transactions
- Per-IP rate limiting on challenge/download

## Run

```
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`

Test users:
- authority / password (role: AUTHORITY)
- owner / password (role: DATA_OWNER)

## Flows

- Upload: AES-GCM encrypts file → ciphertext stored on disk → policy stored on file
- Challenge: `/files/{id}/challenge` returns small JSON (no payload served)
- Download: `/files/{id}/download` checks attributes satisfy policy; logs transaction; rate-limited
- Key retrieval (CP-ABE simulated): `/files/{id}/key` returns base64 AES key if attributes satisfy the policy

## EDoS Tests

1) Challenge gating
- Send 1000 requests to `/files/{id}/challenge` and verify server returns small JSON, not file bytes.

2) Unauthorized download
- Login as a user without required attributes.
- Request `/files/{id}/download` repeatedly.
- Expected: 403 responses; system does not transmit ciphertext.

3) Authorized vs Unauthorized latency
- Measure response times for authorized download vs unauthorized.
- Expected: unauthorized remains cheap; authorized performs actual file I/O.

## Performance Checks

- Measure upload and download times for 10MB file.
- Monitor CPU and memory during challenge storm; expected resource usage remains bounded.

## Next Steps

- Replace simulated CP-ABE key endpoint with real CP-ABE library (wrap AES key).
- Add user management and registration flows.
- Add S3 backend for storage.
