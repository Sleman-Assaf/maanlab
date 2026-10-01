#!/usr/bin/env bash
# Set up (or update) MAAN LAB on PythonAnywhere. Safe to run again after every `git pull`.
#
#   git clone --depth 1 https://github.com/Sleman-Assaf/maanlab.git ~/maanlab
#   bash ~/maanlab/deploy/pythonanywhere_setup.sh
#
# Creates the virtualenv, a private .env with a fresh secret key (first run only),
# migrates, loads the site content (first run only), compiles translations, collects
# static files, writes the WSGI file and reloads the web app.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
USER_NAME="$(whoami)"
DOMAIN="$(echo "${USER_NAME}" | tr "[:upper:]" "[:lower:]").pythonanywhere.com"
WSGI_FILE="/var/www/${DOMAIN//./_}_wsgi.py"
PY_BIN="$(command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3.10)"

cd "$APP_DIR"
echo "==> App: $APP_DIR  Domain: $DOMAIN  Python: $PY_BIN"

[ -d .venv ] || "$PY_BIN" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
  SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(50))')"
  umask 077
  cat > .env <<EOF
DJANGO_SECRET_KEY=${SECRET}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=${DOMAIN}
DJANGO_CSRF_TRUSTED_ORIGINS=https://${DOMAIN}
SITE_URL=https://${DOMAIN}
# HTTPS is enforced by PythonAnywhere ("Force HTTPS" on the Web tab).
DJANGO_BEHIND_PROXY=True
DJANGO_SECURE_SSL_REDIRECT=False
EOF
  echo "==> Wrote .env (secret key generated on this server)"
fi

.venv/bin/python manage.py migrate --noinput

COUNT="$(.venv/bin/python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from projects.models import Project; print(Project.objects.count())")"
if [ "$COUNT" = "0" ]; then
  .venv/bin/python manage.py loaddata deploy/site_data.json
  echo "==> Loaded site content"
fi

.venv/bin/python manage.py compile_translations
.venv/bin/python manage.py collectstatic --noinput

VENV_SITE="$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
if [ -f "$WSGI_FILE" ]; then
  cat > "$WSGI_FILE" <<EOF
# Managed by maanlab/deploy/pythonanywhere_setup.sh
import os
import sys

# Use the project's virtualenv packages first, even if the Web tab's virtualenv
# setting is missing (the system site-packages also ships a different Django).
for entry in ("${VENV_SITE}", "${APP_DIR}"):
    if entry not in sys.path:
        sys.path.insert(0, entry)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
EOF
  touch "$WSGI_FILE"   # reloads the web app
  echo "==> WSGI file updated and web app reloaded"
else
  echo "!! Web app not created yet: create it on the Web tab (Manual configuration), then run this script again."
fi

.venv/bin/python manage.py check --deploy || true
echo "==> Done: https://${DOMAIN}/"
