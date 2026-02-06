Summary

This folder contains a sample `systemd` unit and quick instructions to run the Flask app with Gunicorn and TLS (port 443).

Quick steps

- Install gunicorn (preferably inside your virtualenv):

```bash
# activate your virtualenv first (example)
source /path/to/venv/bin/activate
pip install gunicorn
```

- Run Gunicorn directly (quick test, uses sudo to bind 443):

```bash
sudo /path/to/venv/bin/gunicorn --certfile /etc/letsencrypt/live/your.domain/fullchain.pem \
  --keyfile /etc/letsencrypt/live/your.domain/privkey.pem -w 4 -b 0.0.0.0:443 cba.app:app
```

- To run as a service (recommended), copy `gunicorn_https.service` to `/etc/systemd/system/`, edit placeholders:
  - `WorkingDirectory` → absolute path to repository root (where `cba` package lives)
  - `Environment` PATH → path to your virtualenv `bin`
  - `ExecStart` → same as the run command, with absolute paths for `gunicorn`, `fullchain.pem`, and `privkey.pem`
  - `User`/`Group` → choose unprivileged user (e.g. `www-data`)

Then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn_https.service
sudo systemctl start gunicorn_https.service
sudo systemctl status gunicorn_https.service
```

Notes and safety

- Binding to port 443 requires root privileges; using `sudo` or systemd is usual. For improved security consider running Gunicorn on a high port and using a reverse proxy (nginx) to terminate TLS.
- Replace all `/path/to/...` placeholders with real absolute paths on your server.
- Ensure `SECRET_KEY` and any production env vars are set in a secure way (systemd `EnvironmentFile` or `Environment=` lines).

Testing

- From another machine try:

```bash
curl -I https://your.domain --insecure
```

- Open the site in a browser and verify TLS certificate is valid.
