#!/usr/bin/env bash
# One-liner helper to deploy the Apache api-proxy to the DMZ host
# - Enforces use of the 'two' user (admin is not supported on the DMZ)
# - Safeguards: dry-run, backup existing site, syntax-check before reload
# Usage examples:
#  ./deploy_apache_dmz_one_liner.sh                     # uses default two@192.168.178.41
#  SSH_TARGET=two@192.168.178.41 ./deploy_apache_dmz_one_liner.sh --cert
#  DRY_RUN=1 ./deploy_apache_dmz_one_liner.sh

set -euo pipefail
: ${SSH_TARGET:=two@192.168.178.41}
: ${LOCAL_CONF:="specs/006-nextcloud-litellm-infra/configs/apache-api-proxy.conf"}
: ${REMOTE_SITES_DIR:=/etc/apache2/sites-available}
: ${REMOTE_TMP:=/tmp/lemonade_api_proxy.conf}
: ${DRY_RUN:=0}

echo "Deploy helper — target=${SSH_TARGET}  (local conf=${LOCAL_CONF})"
if [ "${DRY_RUN}" != "0" ]; then
  echo "DRY RUN: no remote changes will be applied" >&2
fi

# ensure ssh user is 'two'
remote_user=${SSH_TARGET%%@*}
if [ "$remote_user" != "two" ]; then
  echo "ERROR: deploy to DMZ must use user 'two' (remote user: $remote_user). Aborting." >&2
  exit 2
fi

# basic local checks
if [ ! -f "${LOCAL_CONF}" ]; then
  echo "ERROR: local config not found: ${LOCAL_CONF}" >&2
  exit 3
fi

ssh_opts=( -o BatchMode=yes -o ConnectTimeout=10 )
ssh ${ssh_opts[*]} "$SSH_TARGET" -- true || { echo "ERROR: cannot SSH to ${SSH_TARGET}" >&2; exit 4; }

if [ "$DRY_RUN" != "0" ]; then
  echo "DRY-RUN: scp ${LOCAL_CONF} ${SSH_TARGET}:${REMOTE_TMP}";
  echo "DRY-RUN: ssh ${SSH_TARGET} 'sudo cp ${REMOTE_TMP} ${REMOTE_SITES_DIR}/api-proxy.conf && sudo a2enmod proxy proxy_http ssl headers rewrite && sudo a2ensite api-proxy && sudo apache2ctl -t && sudo systemctl reload apache2'";
  exit 0
fi

# copy and deploy
scp "${LOCAL_CONF}" "${SSH_TARGET}:${REMOTE_TMP}"
ssh ${ssh_opts[*]} "$SSH_TARGET" bash -s <<'REMOTE'
set -euo pipefail
REMOTE_TMP='/tmp/lemonade_api_proxy.conf'
REMOTE_SITES_DIR='/etc/apache2/sites-available'
BACKUP_DIR="/var/backups/lemonade_api_proxy"
sudo mkdir -p "$BACKUP_DIR"
if [ -f "$REMOTE_SITES_DIR/api-proxy.conf" ]; then
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  sudo cp "$REMOTE_SITES_DIR/api-proxy.conf" "$BACKUP_DIR/api-proxy.conf.$ts"
  echo "backed up existing api-proxy.conf -> $BACKUP_DIR/api-proxy.conf.$ts"
fi
sudo cp "$REMOTE_TMP" "$REMOTE_SITES_DIR/api-proxy.conf"
sudo chown root:root "$REMOTE_SITES_DIR/api-proxy.conf" && sudo chmod 0644 "$REMOTE_SITES_DIR/api-proxy.conf"
# enable modules and site
sudo a2enmod proxy proxy_http ssl headers rewrite || true
sudo a2ensite api-proxy || true
# validate and reload
sudo apache2ctl -t
sudo systemctl reload apache2
# short smoke: ensure site config exists
sudo ls -l "$REMOTE_SITES_DIR/api-proxy.conf"
REMOTE

echo "Deployed config to ${SSH_TARGET} and reloaded Apache. Run tests/dmz_smoke.sh from a host that resolves api.makerspace.ch to the DMZ IP."

echo "Recommended smoke-test (developer laptop):"
echo "  sudo -- sh -c \"echo '192.168.178.41 api.makerspace.ch' >> /etc/hosts\""
echo "  bash specs/006-nextcloud-litellm-infra/tests/dmz_smoke.sh"

echo "If you want, rerun with DRY_RUN=1 to simulate."