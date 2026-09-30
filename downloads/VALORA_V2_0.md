# VALORA v2.0 — Mobile UI Foundation

This release establishes the first Flutter application shell:

- Login screen
- Dashboard
- Portfolio summary model
- Backend API client
- Material 3 dark theme
- Buy Points / Invest entry points

## Production rules

1. Login must call the real authentication endpoint.
2. Tokens must be stored securely.
3. Dashboard values must come from the VALORA backend.
4. No Binance credentials belong in the mobile application.
5. Investment actions must require backend authorization and provider confirmation.
6. Displayed NAV must carry a freshness timestamp.
7. Points and investment NAV remain separate accounting domains.
