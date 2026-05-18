# Deployment Guide

This repository supports:

1. Manual deployment with non-root user (`deploy.sh`)
2. GitHub Actions auto deployment (`.github/workflows/deploy.yml`)
3. HTTPS setup with certbot (`scripts/enable_https_certbot.sh`)

## 1) Manual deployment (recommended)

From this project folder:

```bash
chmod +x deploy.sh
SERVER_HOST=47.98.235.65 \
SERVER_WEB_ROOT=/usr/share/nginx/html \
SERVER_PORT=22 \
SERVER_USER=deploy \
SSH_KEY_PATH=~/.ssh/id_ed25519_deploy \
./deploy.sh
```

If you want to sync WeChat Mini Program `Milestone` progress automatically after deploy, add these optional vars:

```bash
MILESTONE_WEBHOOK_URL=https://your-flask-api.com/api/milestones/travel-sync \
MILESTONE_WEBHOOK_TOKEN=your_webhook_token \
./deploy.sh
```

Webhook payload sent by `deploy.sh`:

```json
{
	"event": "travel_photos_updated",
	"page": "travel.html",
	"milestone": "Nice",
	"photo_count": 3,
	"photos": ["media/nice-01.jpg", "media/nice-02.jpg", "media/nice-03.jpg"],
	"deployed_url": "http://47.98.235.65/travel.html",
	"deployed_at": "2026-05-06-090000"
}
```

Notes:

- `SERVER_USER` defaults to `deploy`.
- Backups are stored in `${SERVER_WEB_ROOT}/.deploy-backups/<timestamp>/`.

## WeChat Mini Program release check

Use the existing CLI helper before release:

```bash
./scripts/wechat_release_check.sh
```

What it checks before calling WeChat DevTools CLI:

- `app.json` permission `desc` is present and within the 30-character limit.
- Empty optional runtime config is surfaced as warnings, including `QQ_MAP_KEY`, `CLOUD_ENV_ID`, and tag analysis endpoints.
- Then it runs the full release chain: `islogin -> preview -> upload`.

## 2) Create/repair deploy user on server

Use this script if deploy user is missing or permissions need reset:

```bash
chmod +x scripts/setup_deploy_user.sh
SERVER_HOST=47.98.235.65 \
ROOT_SSH_KEY=~/.ssh/id_ed25519_deploy \
DEPLOY_PUBKEY_PATH=~/.ssh/id_ed25519_deploy.pub \
SERVER_WEB_ROOT=/usr/share/nginx/html \
./scripts/setup_deploy_user.sh
```

## 3) GitHub Actions auto deployment

Create these repository secrets:

- `SERVER_HOST` (example: `47.98.235.65`)
- `SERVER_PORT` (example: `22`)
- `SERVER_WEB_ROOT` (example: `/usr/share/nginx/html`)
- `DEPLOY_USER` (example: `deploy`)
- `DEPLOY_SSH_KEY` (private key content of `~/.ssh/id_ed25519_deploy`)

Then:

- Push to `main` branch to deploy automatically.
- Or run manually from GitHub Actions -> `Deploy Personal Site` -> `Run workflow`.

## 4) Enable HTTPS (domain required)

Let's Encrypt needs a domain name. IP-only HTTPS cert is not supported in normal certbot flow.

When your DNS A record points to this server, run:

```bash
chmod +x scripts/enable_https_certbot.sh
SERVER_HOST=47.98.235.65 \
DOMAIN=your-domain.com \
EMAIL=you@example.com \
ROOT_SSH_KEY=~/.ssh/id_ed25519_deploy \
./scripts/enable_https_certbot.sh
```

## 5) How to find nginx root path

```bash
ssh -i ~/.ssh/id_ed25519_deploy root@47.98.235.65
nginx -T | grep -E "server_name|root" -n
```

Use the active `root` value as `SERVER_WEB_ROOT`.

## 6) Flask API side (Milestone sync)

In your Flask backend, add an endpoint to accept this webhook and update your Mini Program milestone record.

Suggested behavior:

- Verify `Authorization: Bearer <token>`.
- Validate `event == travel_photos_updated`.
- Upsert milestone by key like `travel_nice`.
- Save `photo_count`, `photos`, `deployed_at`, `deployed_url`.
- Return JSON `{ "ok": true }`.

## 7) FastAPI backend (CMS)

Backend path in this repo:

- `backend/app/main.py`
- `backend/app/templates/admin.html`

One-command remote setup (uploads backend code, installs deps, creates systemd service):

```bash
chmod +x scripts/setup_backend_remote.sh
SERVER_HOST=47.98.235.65 \
SERVER_USER=deploy \
SSH_KEY_PATH=~/.ssh/id_ed25519_deploy \
./scripts/setup_backend_remote.sh
```

Nginx reverse proxy snippet helper:

```bash
chmod +x scripts/setup_nginx_backend_proxy.sh
SERVER_HOST=47.98.235.65 \
SERVER_USER=deploy \
SSH_KEY_PATH=~/.ssh/id_ed25519_deploy \
./scripts/setup_nginx_backend_proxy.sh
```

After setup:

- Health check: `http://47.98.235.65/api/health`
- Admin panel: `http://47.98.235.65/admin` (HTTP Basic auth)

### Important: change admin credentials

Update service env values and restart backend:

```bash
ssh -i ~/.ssh/id_ed25519_deploy root@47.98.235.65
sed -i 's/Environment=ADMIN_USERNAME=.*/Environment=ADMIN_USERNAME=your_admin/' /etc/systemd/system/une-vie-backend.service
sed -i 's/Environment=ADMIN_PASSWORD=.*/Environment=ADMIN_PASSWORD=your_strong_password/' /etc/systemd/system/une-vie-backend.service
systemctl daemon-reload
systemctl restart une-vie-backend
```
