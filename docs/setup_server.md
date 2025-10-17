# SloorJuke 24/7 Server Setup Guide

This guide will walk you through setting up your SloorJuke server to run 24/7 on a Linux machine (such as a Raspberry Pi or any Debian/Ubuntu server). The process includes automatic startup, local network discovery, and web access via a custom hostname.

---

## Prerequisites

- **Linux (Debian/Ubuntu recommended)**
- **Python 3.7+**
- **Node.js 22+**
- **VLC Media Player**
- **git**
- **sudo privileges**

---

## 1. Clone the Repository

```bash
git clone https://github.com/sloorjuice/jukebox.git
cd jukebox
```

---

## 2. Install Dependencies

Run the install script to set up Python, Node.js dependencies, and VLC:

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

---

## 3. Run the Setup Script

This script configures your server for 24/7 operation, sets up systemd services, mDNS discovery, and nginx for easy access.

```bash
chmod +x scripts/setup_server.sh
sudo ./scripts/setup_server.sh
```

**What this does:**
- Sets the hostname to `jukebox`
- Installs and configures `avahi-daemon` for `.local` network discovery
- Installs and configures `nginx` to proxy requests to the frontend
- Removes default nginx pages
- Sets up systemd services for automatic backend/frontend startup
- Enables all services to start on boot

---

## 4. Access Your Jukebox

- **Web Frontend:**  
  [http://jukebox.local](http://jukebox.local) (from any device on your local network)
- **API:**  
  [http://jukebox.local:8000](http://jukebox.local:8000)
- **API Docs:**  
  [http://jukebox.local:8000/docs](http://jukebox.local:8000/docs)

---

## 5. Service Management

- **Check service status:**
  ```bash
  sudo systemctl status jukebox-backend.service
  sudo systemctl status jukebox-frontend.service
  sudo systemctl status nginx
  sudo systemctl status avahi-daemon
  ```
- **View logs:**
  ```bash
  sudo journalctl -u jukebox-backend.service -f
  sudo journalctl -u jukebox-frontend.service -f
  sudo journalctl -u nginx.service -f
  ```
- **Restart services:**
  ```bash
  sudo systemctl restart jukebox-backend.service
  sudo systemctl restart jukebox-frontend.service
  sudo systemctl restart nginx
  ```

---

## 6. Automatic Startup

All services are enabled to start automatically on boot. Your jukebox will always be available as long as your server is running.

---

## Troubleshooting

- If you still see the nginx welcome page, restart nginx:
  ```bash
  sudo systemctl restart nginx
  ```
- Ensure your device is connected to the same network as the server.
- For port forwarding or remote access, configure your router to forward ports 80 and 8000 to your server.

---

## Uninstall or Reconfigure

To remove or reconfigure services, use `systemctl disable` and edit the service files in `/etc/systemd/system/`.

---

**Enjoy your 24/7 home jukebox!**