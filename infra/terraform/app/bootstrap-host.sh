#!/bin/bash
set -euo pipefail
umask 077

# This script installs host tooling only. It contains no credentials, does not
# fetch application secrets, and does not expose/start the application.
dnf upgrade --refresh -y
dnf install -y docker awscli2 amazon-ssm-agent jq python3.12
systemctl enable --now docker amazon-ssm-agent

install -d -m 0755 /usr/local/lib/docker/cli-plugins
curl --fail --show-error --location --retry 3 \
  https://github.com/docker/compose/releases/download/v5.7.1/docker-compose-linux-x86_64 \
  --output /usr/local/lib/docker/cli-plugins/docker-compose
printf '%s  %s\n' \
  af426722a8af5de812fcee30cc1c39f0639f5f723cbadefb25e5d4db054064cf \
  /usr/local/lib/docker/cli-plugins/docker-compose | sha256sum --check --status
chmod 0755 /usr/local/lib/docker/cli-plugins/docker-compose

install -d -m 0700 /opt/forgeboard /opt/forgeboard/shared /opt/forgeboard/releases /run/forgeboard
printf 'd /run/forgeboard 0700 root root -\n' > /etc/tmpfiles.d/forgeboard.conf
docker compose version
python3.12 --version
