# Authentication Development

## Responsibilities

Keycloak owns identity concerns:

- usernames, passwords, password reset, and login sessions
- the `employee` and `admin` realm roles
- signed access tokens issued to the browser

WorkHub owns application concerns:

- the local user record linked by Keycloak subject ID
- active or inactive application access
- employee-owned business records and administrator permissions

Passwords and access tokens are never stored in the WorkHub database.

## Login Flow

1. The frontend redirects the user to Keycloak using Authorization Code Flow with PKCE.
2. Keycloak authenticates the user and returns an authorization code.
3. The Keycloak browser adapter exchanges the code for a short-lived access token.
4. The frontend sends that token in the `Authorization: Bearer` header.
5. FastAPI validates the token signature, issuer, expiry, and API audience.
6. FastAPI creates or updates the linked local user profile.
7. A route dependency enforces the required `employee` or `admin` role.

## URL Separation

The access token contains the public issuer that the browser used. The backend must validate that exact value. The backend fetches public signing keys using the private Docker network.

- `KEYCLOAK_PUBLIC_ISSUER_URL`: issuer expected inside the access token
- `KEYCLOAK_INTERNAL_URL`: private address used by FastAPI to fetch signing keys

Keeping these values separate is important when the application later moves behind HTTPS and a reverse proxy.

## Secure Development Access

The browser Web Crypto API required by PKCE is not available on a plain HTTP private-IP origin such as `http://10.20.11.110:3000`. Until the reverse proxy provides HTTPS, forward the server ports to localhost from PowerShell:

```powershell
ssh -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 -L 8080:127.0.0.1:8080 nilaxsan@10.20.11.110
```

Keep that SSH window open and browse to `http://localhost:3000`. The services and data still run on the server; the tunnel only carries browser traffic securely over SSH.

For this development mode, use localhost for these server `.env` values:

- `BACKEND_CORS_ORIGINS=http://localhost:3000`
- `KEYCLOAK_PUBLIC_ISSUER_URL=http://localhost:8080/realms/tcl-workhub`
- `NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080`
- `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`

## Protected Test Routes

- `GET /api/me`: any authenticated WorkHub employee or administrator
- `GET /api/employee`: employee role only
- `GET /api/admin`: administrator role only

These routes prove authentication, profile synchronization, and role authorization before time-tracking development starts.

## Production Follow-up

When the final HTTPS host is available:

1. update Keycloak hostname and proxy settings
2. update the public frontend, backend, and issuer URLs
3. update Keycloak redirect URIs and web origins
4. remove private development origins if they are no longer needed
5. retest login, logout, token refresh, and both role boundaries
