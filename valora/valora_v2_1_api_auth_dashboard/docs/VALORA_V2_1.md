# VALORA v2.1 — Real API Contract

## Added
- Register endpoint
- Login endpoint
- Development session token
- Dashboard summary endpoint
- Auth-aware API client
- Dashboard domain model

## Important
The authentication implementation in this release is development-only.
Before production:
- PostgreSQL user store
- Argon2id/bcrypt
- JWT/opaque session management
- Refresh token rotation
- token revocation
- MFA
- rate limiting
- device/session management
- email verification
- KYC/AML workflow where legally required

## Financial architecture
Dashboard values are read from the backend. The mobile app is not
an accounting authority and never talks directly to Binance.
