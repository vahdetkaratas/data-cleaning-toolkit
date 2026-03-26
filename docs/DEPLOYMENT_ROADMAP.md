# VPS deployment roadmap — step by step

Deploy the Data Cleaning Toolkit on your own VPS with your domain from scratch. This guide uses **Docker**, **docker-compose**, and **Caddy** (reverse proxy + automatic HTTPS). No prior experience required—run the commands in order.

The `docker-compose.yml` in this repo publishes the app only on port **8501**. For a public domain and HTTPS, **Caddy** listens on 80/443 and forwards traffic to **127.0.0.1:8501** inside the server.

---

## What we will do (overview)

1. Connect to the VPS with **SSH**.
2. Install **Docker** and **Docker Compose** on the server.
3. **Copy** the project to the VPS and **run** it with Docker.
4. Install **Caddy** and route your domain to **8501** (reverse proxy; **Let’s Encrypt** is automatic).
5. Point your **domain** at the VPS IP (DNS).

Then the app is available at `https://YOUR_DOMAIN` (e.g. `https://app.example.com`).

---

## 0. Prerequisites (on your computer)

- **VPS:** IP address (e.g. `203.0.113.10`), username (often `root`), password or SSH key.
- **Domain:** A domain you control and can edit DNS for (we will add an A record).
- **SSH client:**
  - **Windows:** PowerShell or Windows Terminal (OpenSSH is usually preinstalled). Alternative: [PuTTY](https://www.putty.org/).
  - **Mac/Linux:** The `ssh` command in Terminal.

---

## 1. First SSH connection to the VPS

### Windows (PowerShell or Terminal)

```powershell
ssh root@YOUR_VPS_IP
```

Example: `ssh root@203.0.113.10`  
If prompted for a password, use the one from your provider (input is hidden; press Enter when done).

### Mac / Linux

```bash
ssh root@YOUR_VPS_IP
```

After connecting, your prompt should look like `root@hostname:~#`. You are now running commands **on the VPS**.

---

## 2. Update the system

After you connect, run:

**Debian / Ubuntu:**

```bash
apt update && apt upgrade -y
```

**CentOS / Rocky / Alma:**

```bash
dnf update -y
```

The steps below are written for **Debian/Ubuntu**. On another distribution, search for “Docker install [distro name]” and adjust the Docker section accordingly.

---

## 3. Install Docker

Docker runs the app in a container so you do not install Python directly on the host and get the same environment everywhere.

### 3.1 Install Docker (Debian/Ubuntu)

```bash
apt install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a644 /etc/apt/keyrings/docker.asc

# Ubuntu:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
# For Debian only, replace the line above (ubuntu → debian):
# echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify:

```bash
docker --version
docker compose version
```

Both should print a version string.

---

## 4. Get the project onto the VPS

Two options: **Git** (preferred) or **copy files**.

### Option A: Git (if the repo is on GitHub)

```bash
apt install -y git
cd /opt
git clone https://github.com/your-username/data-cleaning-toolkit.git
cd data-cleaning-toolkit
```

Replace `your-username` with your GitHub user or organization; update the URL if the repo name differs. Use a personal access token if the repo is private; for a public repo this is enough.

### Option B: Copy from your computer

From your project folder (PowerShell / Terminal):

```bash
scp -r . root@YOUR_VPS_IP:/opt/data-cleaning-toolkit
```

On the VPS:

```bash
cd /opt/data-cleaning-toolkit
```

You should see `Dockerfile`, `docker-compose.yml`, `src/`, `data/`, `requirements.txt`, etc.

---

## 5. Run the app with Docker

On the VPS, from the project directory:

```bash
cd /opt/data-cleaning-toolkit
docker compose up -d --build
```

- `--build` rebuilds the image from the project.  
- `-d` runs in the background.

Check:

```bash
docker compose ps
```

The `app` service should show **Up**. In a browser, try:

`http://YOUR_VPS_IP:8501`

If it loads, Streamlit is running. In production, **do not** expose **8501** to the internet directly—only via **Caddy** on your domain.

---

## 6. Install Caddy (reverse proxy + HTTPS)

**Caddy** listens on ports 80 and 443, forwards to Streamlit at `127.0.0.1:8501`, and when DNS is correct it **automatically** obtains and renews **Let’s Encrypt** certificates (no Certbot needed on this path).

### 6.1 Install Caddy (Debian / Ubuntu)

Summary aligned with the [official Caddy install docs](https://caddyserver.com/docs/install):

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy
```

### 6.2 Create the Caddyfile

```bash
nano /etc/caddy/Caddyfile
```

Remove any default sample content and add a block like below; replace **`YOUR_DOMAIN`** with your real hostname (e.g. `app.example.com`):

```caddyfile
YOUR_DOMAIN {
    request_body {
        max_size 50MB
    }
    reverse_proxy 127.0.0.1:8501
}
```

Save: `Ctrl+O`, Enter, exit: `Ctrl+X`.

### 6.3 Apply configuration

```bash
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
systemctl enable caddy
```

If `validate` succeeds, continue. On errors, check logs: `journalctl -u caddy -e`.

**HTTPS:** After the A record points to the VPS and has propagated, Caddy will request the certificate on first use. If DNS is not ready yet, you may see certificate errors; verify DNS and run `systemctl reload caddy` again.

---

## 7. Point your domain at the VPS (DNS)

At your registrar or DNS host (GoDaddy, Namecheap, Cloudflare, etc.), edit DNS:

- **Type:** A  
- **Host / name:** `app` (or `@` for apex—depends on the provider)  
- **Value:** your VPS **public IP**  
- TTL: 300 or 3600

Example: for `app.example.com`, host `app`, value `203.0.113.10`.  
Save and wait for propagation (minutes to hours). Then try `http://YOUR_DOMAIN` in a browser; Caddy proxies to 8501. If the app is down you might see a **502**—check `docker compose ps`.

---

## 8. HTTPS note (Caddy)

On this path you **do not need Certbot**: Caddy uses **Let’s Encrypt** when the domain resolves correctly. If `https://YOUR_DOMAIN` loads in the browser, you are done.

---

## 9. Firewall

Open only what you need:

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

22: SSH, 80: HTTP (ACME / redirects), 443: HTTPS. **Do not** open **8501** publicly—only **Caddy** should reach `127.0.0.1:8501` from inside the server.

---

## 10. Persistence after reboot

`docker-compose.yml` uses `restart: unless-stopped`, so the container comes back after a VPS reboot. Caddy is enabled as a service (`systemctl enable caddy`).

Check:

```bash
docker compose ps
systemctl status caddy --no-pager
```

You want the container **Up** and Caddy **active**.

---

## 11. Updating when you push new code

If you use Git:

```bash
cd /opt/data-cleaning-toolkit
git pull
docker compose up -d --build
```

If you deploy with `scp`, upload changes and run the same `docker compose up -d --build`.

---

## 12. Troubleshooting

| Issue | What to do |
|--------|------------|
| `http://IP:8501` does not load | `docker compose ps` and `docker compose logs -f`—is the container running, any errors? |
| Domain does not resolve | DNS: `ping YOUR_DOMAIN` or `dig YOUR_DOMAIN`—does it show the VPS IP? **Caddy:** `caddy validate --config /etc/caddy/Caddyfile`, `journalctl -u caddy -e`. |
| 502 Bad Gateway | Caddy cannot reach 8501. On the VPS, try `curl -sS http://127.0.0.1:8501`; confirm `docker compose ps` shows `app` **Up**. |
| HTTPS / certificate errors | Confirm A record to VPS, ports 80/443 open; wait for DNS, then `systemctl reload caddy`. |

---

## 13. Command cheat sheet (copy-paste)

First-time setup on Debian/Ubuntu as **root**—add the full Docker block from **§3** before this; then:

```bash
apt install -y git debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy
cd /opt && git clone https://github.com/your-username/data-cleaning-toolkit.git
cd data-cleaning-toolkit
docker compose up -d --build
# Then edit /etc/caddy/Caddyfile: YOUR_DOMAIN + reverse_proxy 127.0.0.1:8501 (§6.2)
caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy
ufw allow 22,80,443 && ufw enable
```

Do not forget the A record in DNS pointing to the VPS IP.

---

## Deploy assets in this repository

- **Dockerfile:** Image definition for the app.  
- **docker-compose.yml:** Build and run (port **8501**).  
- **Caddyfile:** Lives on the server at `/etc/caddy/Caddyfile`; see **§6.2** for an example.

---

## Optional: Nginx

If you prefer **Nginx**, it can play the same role: listen on 80/443 and `proxy_pass http://127.0.0.1:8501` to Streamlit; use **Certbot** with `certbot --nginx` for TLS. The **primary** path in this guide is **Caddy**; Nginx is an alternative only.

Following this guide, the app is served on your own domain over HTTPS on the VPS.
