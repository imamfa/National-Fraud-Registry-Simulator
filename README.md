<div align="center">

# 🛡️ National Fraud Registry Simulator

**Zero Trust API Security Lab — JOSE-based B2B Anti-Fraud Data Exchange**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![KrakenD](https://img.shields.io/badge/KrakenD-API%20Gateway-FF6B35?style=flat-square)](https://krakend.io)
[![Vault](https://img.shields.io/badge/HashiCorp-Vault-black?style=flat-square&logo=vault&logoColor=FFEC6E)](https://vaultproject.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> A hands-on security lab demonstrating **Edge Security** vs **Backend Processing** separation using JOSE standards (JWS · JWE · JWK · JWKS) and **GPG-based batch file transfer** via SFTP — designed to simulate two distinct secure transmission channels between a national regulator and Payment Service Providers (PSP).

</div>

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Security Model](#security-model)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Simulation Scenarios](#simulation-scenarios)
- [Systemd Services](#systemd-services)
- [Security Notes](#security-notes)
- [References](#references)

---

## Overview

The **National Fraud Registry (NFR) Simulator** is a lab environment that demonstrates how a national regulator can securely exchange fraud-related data with Payment Service Providers using a Zero Trust architecture across **two transmission channels**: real-time API and batch file transfer.

### Core Design Principles

| Principle | Implementation |
|---|---|
| **Zero Trust Network Access** | Every request and file must be explicitly verified — no implicit trust |
| **Segregation of Duties** | Edge security is decoupled from backend business logic |
| **Defense in Depth** | Multiple layers: signature validation → decryption → processing |
| **Least Privilege** | Private keys are isolated inside HashiCorp Vault |
| **Dual-Channel Security** | API channel uses JOSE (JWE/JWS); batch channel uses GPG asymmetric encryption |

### What This Lab Demonstrates

- How an **API Gateway acts as a Policy Enforcement Point (PEP)** — rejecting forged requests before they reach internal services
- How **JWE + JWS** can be combined to achieve both **confidentiality** and **authenticity** on real-time API traffic
- How **JWKS** enables dynamic public key distribution without hardcoding
- How **HashiCorp Vault** separates secret management from application runtime
- How **GPG asymmetric encryption + signature verification** secures batch file transmission over SFTP
- How a **Python Watchdog service** automates real-time file processing from a dropzone directory

---

## Architecture

### Channel 1 — Real-Time API (JOSE/HTTPS)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    PSP CLIENT (Streamlit — HTTPS)                     │
│   Build Payload → Encrypt (JWE) → Sign (JWS) → Send to Gateway      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTPS (TLS Self-Signed)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    EDGE SECURITY (KrakenD Gateway)                    │
│                                                                       │
│   1. Receive inbound request                                          │
│   2. Fetch public key from JWKS endpoint (Nginx)                     │
│   3. Validate JWS signature                                           │
│   4. Reject forged/invalid requests ───────────────► HTTP 401        │
│   5. Forward valid requests downstream                                │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ Internal traffic (validated only)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    BACKEND APPLICATION (FastAPI)                      │
│                                                                       │
│   1. Receive validated request                                        │
│   2. Fetch private key from HashiCorp Vault                          │
│   3. Decrypt JWE payload                                              │
│   4. Execute business logic                                           │
│   5. Return response ───────────────────────────────► HTTP 200       │
└─────────────────────┬────────────────────────────────────────────────┘
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
┌──────────────────┐   ┌──────────────────┐
│  HashiCorp Vault │   │  Nginx (JWKS)    │
│  Private Key     │   │  Public Key      │
│  Storage         │   │  Distribution    │
└──────────────────┘   └──────────────────┘
```

### Channel 2 — Batch File Transfer (GPG/SFTP)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PSP CLIENT (SFTP)                             │
│   Encrypt File (GPG) → Sign (GPG Signature) → Upload via SFTP       │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ SFTP (port 2222)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│               SFTP DROPZONE  (sftp_data/psp_user/upload/)             │
│                   Incoming *.gpg files land here                      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ inotify / PollingObserver
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   PYTHON WATCHDOG (regulator_watchdog.py)             │
│                                                                       │
│   1. Detect new *.gpg file in dropzone                               │
│   2. Fetch regulator private key + PSP public key from Vault         │
│   3. Decrypt GPG file (asymmetric)                                   │
│   4. Verify PSP signature                                             │
│   5a. Valid   → move to processed/, flush decrypted payload to log   │
│   5b. Tampered → reject, log [ERROR]                                 │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 🔴 Edge Security — KrakenD API Gateway
The gateway acts as the **Policy Enforcement Point**. No request reaches the backend without passing signature validation.

- Receive inbound API requests from PSP clients
- Retrieve public key from JWKS endpoint
- Validate JSON Web Signature (JWS)
- Reject forged or tampered requests at the perimeter
- Forward only verified requests to the backend

#### 🟢 Backend Application — FastAPI
The backend only receives traffic that has already been authenticated by the gateway. Its sole focus is business logic.

- Receive pre-validated requests from the gateway
- Retrieve private key from Vault
- Decrypt JWE payload
- Execute fraud registry business logic
- Return structured response

#### 🟠 Batch Processor — Python Watchdog
The watchdog service monitors the SFTP dropzone and processes GPG-encrypted files autonomously.

- Poll `sftp_data/psp_user/upload/` for new `*.gpg` files using `PollingObserver`
- Retrieve regulator private key and PSP public key from HashiCorp Vault at startup
- Decrypt incoming GPG files using regulator private key
- Verify PSP signature to ensure file authenticity and integrity
- Move valid files to `processed/`; reject and log tampered files
- Flush decrypted payload content to systemd journal in real-time

#### 🔐 Key Management — HashiCorp Vault
Vault ensures private keys never live inside application code or environment variables.

- Store backend JWE private key and GPG private key securely
- Store PSP GPG public key for signature verification
- Provide key material at runtime for both API and batch channels
- Separate secret lifecycle from application deployment

#### 🌐 Public Key Distribution — Nginx
Nginx acts as a lightweight JWKS server, simulating how a real regulator would publish its public keys.

- Serve `/jwks.json` endpoint
- Expose public key material for JWS validation
- Simulate real-world key distribution infrastructure

#### 💻 Client Simulator — Streamlit (HTTPS)
The Streamlit dashboard runs over HTTPS using a TLS self-signed certificate and simulates PSP-side behavior, including both legitimate and forged request scenarios.

- Accessible via `https://<host>:8501` — encrypted in transit
- Build sample fraud event payload
- Encrypt payload using JWE
- Sign request using JWS
- Toggle between valid and forged signing keys

---

## Security Model

This lab implements two complementary cryptographic standards depending on the transmission channel.

### Channel 1 — JOSE Standards (Real-Time API)

| Standard | RFC | Purpose |
|---|---|---|
| **JWS** | [RFC 7515](https://datatracker.ietf.org/doc/html/rfc7515) | Request authentication and integrity validation |
| **JWE** | [RFC 7516](https://datatracker.ietf.org/doc/html/rfc7516) | Payload confidentiality (end-to-end encryption) |
| **JWK** | [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517) | JSON representation of cryptographic key material |
| **JWKS** | [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517) | Public key set distribution endpoint |

### Channel 2 — OpenPGP Standard (Batch File Transfer)

| Standard | Purpose |
|---|---|
| **GPG Asymmetric Encryption** | File confidentiality — encrypted with regulator public key |
| **GPG Signature Verification** | File authenticity — signed with PSP private key, verified against PSP public key |

### API Request Lifecycle

```
PSP Client                Gateway                  Backend
    │                        │                        │
    │  1. Build JSON payload  │                        │
    │  2. Encrypt → JWE       │                        │
    │  3. Sign    → JWS       │                        │
    │──── HTTPS POST ────────►│                        │
    │                         │  4. Fetch JWKS         │
    │                         │◄────── /jwks.json ─────│── (Nginx)
    │                         │  5. Validate JWS       │
    │◄── 401 Unauthorized ────│  (if invalid)          │
    │                         │                        │
    │                         │─── Forward request ───►│
    │                         │                        │  6. Fetch key (Vault)
    │                         │                        │  7. Decrypt JWE
    │                         │                        │  8. Process logic
    │◄────────── 200 OK ───────────────────────────────│
```

### Batch File Lifecycle

```
PSP Client              SFTP Server             Watchdog Service
    │                        │                        │
    │  1. Encrypt file (GPG) │                        │
    │  2. Sign file   (GPG)  │                        │
    │──── SFTP upload ───────►│                        │
    │                         │  3. File lands in      │
    │                         │     dropzone/          │
    │                         │──── inotify event ────►│
    │                         │                        │  4. Fetch keys (Vault)
    │                         │                        │  5. Decrypt GPG
    │                         │                        │  6. Verify signature
    │                         │              [TAMPERED]│──► log [ERROR], discard
    │                         │                        │  7. Move → processed/
    │                         │                        │  8. Flush payload → journald
```

---

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| Client Simulator | [Streamlit](https://streamlit.io) | Interactive PSP dashboard (HTTPS) |
| API Gateway | [KrakenD](https://krakend.io) | Edge security / Policy Enforcement Point |
| Backend API | [FastAPI](https://fastapi.tiangolo.com) | Business logic processing |
| Batch Processor | [Python Watchdog](https://python-watchdog.readthedocs.io) | Directory polling & GPG file processing |
| File Encryption | [GnuPG](https://gnupg.org) | PGP asymmetric encryption & signature verification |
| Key Management | [HashiCorp Vault](https://vaultproject.io) | Secrets and private key storage |
| JWKS Server | [Nginx](https://nginx.org) | Public key distribution |
| JOSE Library | [jwcrypto](https://jwcrypto.readthedocs.io) | JWS/JWE/JWK implementation |
| SFTP Server | [atmoz/sftp](https://github.com/atmoz/sftp) | Secure batch file ingestion |
| Infrastructure | [Docker Compose](https://docs.docker.com/compose/) | Local container orchestration |

---

## Project Structure

```
nfr-lab/
├── simulate_dashboard.py           # Streamlit PSP client simulator (HTTPS)
├── setup_api_keys.py               # JOSE cryptographic key generation script
├── regulator_watchdog.py           # Python Watchdog — GPG batch file processor
├── vault_init.sh                   # Vault seeding script (keys + secrets)
├── docker-compose.yml              # Container orchestration (KrakenD, Vault, Nginx, SFTP)
│
├── regulator_internal/
│   ├── core_api.py                 # FastAPI backend — decrypt JWE, process logic
│   └── regulator_private_jwe.json # Regulator JWE private key (generated, not committed)
│
├── psp_public/
│   ├── jwks.json                   # PSP JWS public key — served by Nginx
│   └── regulator_jwks.json        # Regulator JWE public key — used by dashboard
│
├── sftp_data/
│   └── psp_user/
│       ├── upload/                 # SFTP dropzone — Watchdog monitors this directory
│       └── processed/             # Decrypted & verified files land here
│
├── krakend_config/
│   └── krakend.json               # KrakenD gateway configuration
│
├── psp_private_jws.json            # PSP JWS private key (lab only, do not commit)
└── README.md
```

> ⚠️ **Note:** `psp_private_jws.json` and any `*.json` key files under `regulator_internal/` should never be committed in a real environment. They are present here for lab simulation purposes only.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- GnuPG (`gpg`) installed on host
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/nfr-lab.git
cd nfr-lab
```

### 2. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install fastapi uvicorn jwcrypto streamlit watchdog requests pydantic python-gnupg
```

### 4. Generate Cryptographic Materials

Generates JWK key pairs for PSP signing (JWS) and backend encryption (JWE), and writes the public keys to the appropriate JWKS files.

```bash
python3 setup_api_keys.py
```

### 5. Start Infrastructure

```bash
docker compose up -d
```

This brings up:
- **KrakenD** — API Gateway on port `8080`
- **HashiCorp Vault** — Key management on port `8200`
- **Nginx** — JWKS endpoint on port `8081`
- **SFTP Server** — Batch file ingestion on port `2222`

### 6. Initialize Vault and Load Keys

```bash
# Vault initialization and key seeding (JOSE keys + GPG keys + passphrase)
bash vault_init.sh

# Verify Vault is healthy:
docker compose logs vault
```

### 7. Run the Backend Service

```bash
python3 regulator_internal/core_api.py
```

Backend runs on `http://localhost:5000`.

### 8. Run the Watchdog Service

```bash
python3 regulator_watchdog.py
```

Watchdog fetches GPG keys from Vault on startup and begins monitoring `sftp_data/psp_user/upload/`.

### 9. Run the Client Dashboard (HTTPS)

```bash
streamlit run simulate_dashboard.py \
  --server.port 8501 \
  --server.sslCertFile ./certs/cert.pem \
  --server.sslKeyFile  ./certs/key.pem
```

Open `https://localhost:8501` in your browser. Accept the self-signed certificate warning on first access.

---

## Usage

Once all services are running:

**API Channel (Real-Time)**
1. Open the Streamlit dashboard at `https://<host>:8501`
2. Fill in the fraud event form in the sidebar
3. **Transmit Valid Payload** — payload is JWE-encrypted and JWS-signed, forwarded by the gateway to the backend
4. **Inject Forged Signature** — payload is signed with an invalid key, rejected at the gateway

**Batch Channel (SFTP)**
1. Encrypt a file with the regulator's GPG public key and sign it with the PSP private key
2. Upload the `*.gpg` file to the SFTP dropzone: `sftp -P 2222 psp_user@<host>`
3. The Watchdog detects the file, decrypts it, verifies the PSP signature, and moves it to `processed/`
4. Monitor the result in real-time via systemd journal (see [Systemd Services](#systemd-services))

---

## Simulation Scenarios

### ✅ Scenario 1: Valid PSP API Request

Simulates a legitimate fraud event report from a registered PSP via the API channel.

**Flow:**
1. Payload is serialized as JSON
2. Payload is encrypted using **JWE** (recipient: backend public key)
3. Request is signed using **JWS** (signer: valid PSP private key)
4. Dashboard connects via **HTTPS** (TLS self-signed)
5. Gateway fetches public key from JWKS and validates JWS ✓
6. Validated request is forwarded to backend
7. Backend retrieves private key from Vault and decrypts JWE
8. Business logic executes, response returned

**Expected result:**
```
HTTP 200 OK
{
  "status": "RECORDED",
  "message": "Report integrated into NFR Database.",
  "next_action": "Initiating Broadcast Verification for Payment ID: ..."
}
```

---

### ❌ Scenario 2: Forged API Signature

Simulates an attacker injecting a fraudulent request using an unauthorized key.

**Flow:**
1. Payload is encrypted using JWE
2. Request is signed using an **invalid or forged private key**
3. Gateway attempts JWS verification against the JWKS public key
4. Signature mismatch — request is **rejected at the perimeter**
5. Backend never receives the request

**Expected result:**
```
HTTP 401 Unauthorized
{
  "error": "Access Denied — signature verification failed"
}
```

---

### ✅ Scenario 3: Valid GPG Batch File

Simulates a PSP submitting an encrypted batch file via SFTP.

**Flow:**
1. PSP encrypts file with regulator GPG public key
2. PSP signs the file with PSP GPG private key
3. File is uploaded to SFTP dropzone as `*.gpg`
4. Watchdog detects the file, fetches keys from Vault
5. Decryption succeeds, PSP signature is verified ✓
6. File moved to `processed/`, decrypted content flushed to systemd log

**Expected result:**
```
[SUCCESS] Decryption Passed! File: ./sftp_data/psp_user/processed/<filename>
```

---

### ❌ Scenario 4: Tampered GPG File

Simulates an attacker uploading a file signed with an unrecognized key.

**Flow:**
1. File is encrypted but signed with an **unknown or tampered key**
2. Watchdog decrypts but signature verification fails
3. File is **rejected and not moved to processed/**

**Expected result:**
```
[ERROR] Tampered File: decryption failed / bad signature
```

---

## Systemd Services

For persistent deployments, this lab includes systemd service units.

```bash
# Start all services
sudo systemctl start nfr-vault-init nfr-backend nfr-watchdog nfr-dashboard

# Stop all services
sudo systemctl stop nfr-dashboard nfr-backend nfr-watchdog nfr-vault-init

# Check status
sudo systemctl status nfr-dashboard
sudo systemctl status nfr-backend
sudo systemctl status nfr-watchdog
```

### Real-Time Log Monitoring

Decrypted payload content is flushed directly to the systemd journal by both the backend and the watchdog service. Use `journalctl` to observe traffic in real-time:

```bash
# Monitor API backend — shows decrypted JWE payloads and fraud reports
journalctl -u nfr-backend -f

# Monitor Watchdog — shows GPG decryption results, signature status, and file events
journalctl -u nfr-watchdog -f

# Monitor all NFR services simultaneously
journalctl -u nfr-backend -u nfr-watchdog -u nfr-dashboard -f
```

> 💡 **Tip:** In a live demo, run `journalctl -u nfr-watchdog -f` on a second terminal pane while uploading a GPG file via SFTP. The decrypted payload will appear in the log within seconds of the file landing in the dropzone.

---

## Security Notes

> This project is **intended for lab and demonstration purposes only.**

Before adapting this architecture for production, the following must be addressed:

| Area | Recommendation |
|---|---|
| **TLS Certificates** | Replace self-signed certificates with CA-issued certificates (e.g. Let's Encrypt) |
| **Audit Logging** | Centralized, tamper-evident audit log for all API events and file processing |
| **Secret Rotation** | Automated key rotation policy via Vault for both JOSE keys and GPG keys |
| **Rate Limiting** | Per-client rate limits at the gateway layer |
| **Mutual TLS (mTLS)** | Client certificate validation on top of JWS |
| **GPG Key Trust Model** | Replace `always_trust` with explicit fingerprint allowlist |
| **SFTP Credentials** | Replace password auth with SSH key-based authentication |
| **Observability** | Distributed tracing, metrics, and alerting |
| **High Availability** | Multi-instance gateway and backend with load balancing |
| **Vault Hardening** | Strict ACL policies, AppRole auth, audit device enabled |
| **CI/CD Secrets** | Never store keys in source control — use a secrets manager |
| **Admin Endpoint Access Control** | Restrict Vault UI and admin APIs with network ACLs |

---

## References

- [RFC 7515 — JSON Web Signature (JWS)](https://datatracker.ietf.org/doc/html/rfc7515)
- [RFC 7516 — JSON Web Encryption (JWE)](https://datatracker.ietf.org/doc/html/rfc7516)
- [RFC 7517 — JSON Web Key (JWK)](https://datatracker.ietf.org/doc/html/rfc7517)
- [RFC 7518 — JSON Web Algorithms (JWA)](https://datatracker.ietf.org/doc/html/rfc7518)
- [RFC 4880 — OpenPGP Message Format](https://datatracker.ietf.org/doc/html/rfc4880)
- [KrakenD Documentation](https://www.krakend.io/docs/)
- [HashiCorp Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [jwcrypto Documentation](https://jwcrypto.readthedocs.io/en/latest/)
- [GnuPG Documentation](https://www.gnupg.org/documentation/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

---

<div align="center">

Built as a security architecture lab. Not for production use without proper hardening.

</div>
