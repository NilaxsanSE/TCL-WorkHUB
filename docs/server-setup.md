# Server Setup Plan

Target server:

- IP: `10.20.11.110`
- SSH port: `22`
- SSH user: `nilaxsan`
- OS: Debian 13
- access: OpenVPN private network

## Current Development Deployment

The initial development environment is installed at `/opt/tcl-workhub`.

- Docker Engine: installed from Debian packages
- Docker Compose: installed from Debian packages
- Git: installed
- repository: cloned from GitHub on branch `main`
- server `.env`: generated with random secrets and permissions set to `600`
- frontend: port `3000`
- backend: port `8000`
- Keycloak: port `8080`
- PostgreSQL: available only inside the Docker network

The current Keycloak configuration uses development mode while access is limited to the private network. Production mode and HTTPS proxy settings must be completed with the TechCenter reverse proxy before public use.

### Browser Access During Development

Keycloak PKCE needs a secure browser context. Plain HTTP on the private server IP does not provide one, so use an SSH tunnel until HTTPS is configured:

```powershell
ssh -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 -L 8080:127.0.0.1:8080 nilaxsan@10.20.11.110
```

Then open `http://localhost:3000`. Docker and all project data remain on the Debian server.

## After SSH Access Is Available

1. Log in to the server.
2. Confirm OS and disk space.
3. Install Docker Engine and Docker Compose plugin if missing.
4. Create app directory, for example `/opt/tcl-workhub`.
5. Clone this repository.
6. Create production `.env` from `.env.example`.
7. Start services with Docker Compose.
8. Configure Keycloak realm, clients, and roles.
9. Verify internal URLs:
   - frontend: `http://10.20.11.110:3000`
   - backend: `http://10.20.11.110:8000`
   - keycloak: `http://10.20.11.110:8080`
10. Ask the server admin to route public HTTPS through the TechCenter reverse proxy.

## Commands To Run Later

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
```

Docker installation should follow the official Debian instructions at deployment time.

After Docker is installed:

```bash
sudo mkdir -p /opt/tcl-workhub
sudo chown "$USER":"$USER" /opt/tcl-workhub
cd /opt/tcl-workhub
git clone https://github.com/NilaxsanSE/TCL-WorkHUB.git .
cp .env.example .env
docker compose up -d
```

Before production use, all `change-me` values in `.env` must be replaced.
