#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
VENV_DIR="${BACKEND_DIR}/.venv"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Creating virtual environment..."
  python3.12 -m venv "${VENV_DIR}"
else
  echo "Upgrading virtual environment..."
  python3.12 -m venv --upgrade "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

cd "${BACKEND_DIR}"
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

CERT_FILE="${SSL_CERT_FILE:-}"
KEY_FILE="${SSL_KEY_FILE:-}"

if [ -n "${CERT_FILE}" ] || [ -n "${KEY_FILE}" ]; then
  if [ -z "${CERT_FILE}" ] || [ -z "${KEY_FILE}" ]; then
    echo "Both SSL_CERT_FILE and SSL_KEY_FILE must be set when providing a custom cert." >&2
    exit 1
  fi

  if [ ! -f "${CERT_FILE}" ] || [ ! -f "${KEY_FILE}" ]; then
    echo "Provided SSL cert/key not found: ${CERT_FILE} ${KEY_FILE}" >&2
    exit 1
  fi
else
  CERT_DIR="${ROOT_DIR}/data/certs"
  CERT_FILE="${CERT_DIR}/selfsigned.crt"
  KEY_FILE="${CERT_DIR}/selfsigned.key"

  if [ ! -f "${CERT_FILE}" ] || [ ! -f "${KEY_FILE}" ]; then
    echo "Generating self-signed certificate..."
    mkdir -p "${CERT_DIR}"
    CERT_FILE="${CERT_FILE}" KEY_FILE="${KEY_FILE}" SSL_CERT_HOSTS="${SSL_CERT_HOSTS:-}" SSL_CERT_IPS="${SSL_CERT_IPS:-}" python - <<'PY'
from pathlib import Path
import datetime
import ipaddress
import os
import socket

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

cert_path = Path(os.environ["CERT_FILE"])
key_path = Path(os.environ["KEY_FILE"])

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name(
    [
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ]
)

def get_primary_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()

hosts = ["localhost"]
extra_hosts = [h.strip() for h in os.environ.get("SSL_CERT_HOSTS", "").split(",") if h.strip()]
hosts.extend(extra_hosts)
enable_wildcard = os.environ.get("SSL_CERT_WILDCARD", "1").lower() in ("1", "true", "yes", "y")
if enable_wildcard:
    hosts.append("*")

ip_hosts = ["127.0.0.1", "::1"]
primary_ip = get_primary_ip()
if primary_ip:
    ip_hosts.append(primary_ip)
extra_ips = [h.strip() for h in os.environ.get("SSL_CERT_IPS", "").split(",") if h.strip()]
ip_hosts.extend(extra_ips)

san_entries = []
for host in hosts:
    san_entries.append(x509.DNSName(host))
for ip in ip_hosts:
    try:
        san_entries.append(x509.IPAddress(ipaddress.ip_address(ip)))
    except ValueError:
        continue

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
    .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
    .sign(key, hashes.SHA256())
)

key_path.write_bytes(
    key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
)
cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
os.chmod(key_path, 0o600)
PY
  fi
fi

echo "Building frontend..."
cd "${ROOT_DIR}/frontend"
npm install
npm run build

echo "Copying frontend build into backend static directory..."
mkdir -p "${BACKEND_DIR}/app/static"
cp -r dist/* "${BACKEND_DIR}/app/static/"

cd "${BACKEND_DIR}"
echo "Starting app on port 5050..."
exec gunicorn -w 4 -b 0.0.0.0:5050 --worker-class eventlet \
  --certfile "${CERT_FILE}" --keyfile "${KEY_FILE}" wsgi:app
