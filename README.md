<div align="center">

# 🛡️ National Fraud Registry Simulator

**Zero Trust API Security Lab — JOSE-based B2B Anti-Fraud Data Exchange**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![KrakenD](https://img.shields.io/badge/KrakenD-API%20Gateway-FF6B35?style=flat-square)](https://krakend.io)
[![Vault](https://img.shields.io/badge/HashiCorp-Vault-black?style=flat-square&logo=vault&logoColor=FFEC6E)](https://vaultproject.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> A hands-on security lab demonstrating **Edge Security** vs **Backend Processing** separation using JOSE standards (JWS · JWE · JWK · JWKS) — designed to simulate secure fraud data exchange between a national regulator and Payment Service Providers (PSP).

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

The **National Fraud Registry (NFR) Simulator** is a lab environment that demonstrates how a national regulator can securely exchange fraud-related data with Payment Service Providers using a Zero Trust API architecture.

### Core Design Principles

| Principle | Implementation |
|---|---|
| **Zero Trust Network Access** | Every request must be explicitly verified — no implicit trust |
| **Segregation of Duties** | Edge security is decoupled from backend business logic |
| **Defense in Depth** | Multiple layers: signature validation → decryption → processing |
| **Least Privilege** | Private keys are isolated inside HashiCorp Vault |

### What This Lab Demonstrates

- How an **API Gateway acts as a Policy Enforcement Point (PEP)** — rejecting forged requests before they reach internal services
- How **JWE + JWS** can be combined to achieve both **confidentiality** and **authenticity**
- How **JWKS** enables dynamic public key distribution without hardcoding
- How **HashiCorp Vault** separates secret management from application runtime

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PSP CLIENT (Streamlit)                      │
│   Build Payload → Encrypt (JWE) → Sign (JWS) → Send to Gateway     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EDGE SECURITY (KrakenD Gateway)                   │
│                                                                      │
│   1. Receive inbound request                                         │
│   2. Fetch public key from JWKS endpoint (Nginx)                    │
│   3. Validate JWS signature                                          │
│   4. Reject forged/invalid requests ──────────────► HTTP 401        │
│   5. Forward valid requests downstream                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Internal traffic (validated only)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   BACKEND APPLICATION (FastAPI)                      │
│                                                                      │
│   1. Receive validated request                                       │
│   2. Fetch private key from HashiCorp Vault                         │
│   3. Decrypt JWE payload                                             │
│   4. Execute business logic                                          │
│   5. Return response ──────────────────────────► HTTP 200           │
└────────────────────┬──────────────────────────────────────────────--┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│  HashiCorp Vault│   │  Nginx (JWKS)    │
│  Private Key    │   │  Public Key      │
│  Storage        │   │  Distribution    │
└─────────────────┘   └──────────────────┘
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

#### 🔐 Key Management — HashiCorp Vault
Vault ensures private keys never live inside application code or environment variables.

- Store backend private key securely
- Provide key material at runtime for JWE decryption
- Separate secret lifecycle from application deployment

#### 🌐 Public Key Distribution — Nginx
Nginx acts as a lightweight JWKS server, simulating how a real regulator would publish its public keys.

- Serve `/jwks.json` endpoint
- Expose public key material for JWS validation
- Simulate real-world key distribution infrastructure

#### 💻 Client Simulator — Streamlit
The Streamlit dashboard simulates PSP-side behavior, including both legitimate and forged request scenarios.

- Build sample fraud event payload
- Encrypt payload using JWE
- Sign request using JWS
- Toggle between valid and forged signing keys

---

## Security Model

This lab implements **JOSE (JSON Object Signing and Encryption)** as its cryptographic foundation.

### Standards Used

| Standard | RFC | Purpose |
|---|---|---|
| **JWS** | [RFC 7515](https://datatracker.ietf.org/doc/html/rfc7515) | Request authentication and integrity validation |
| **JWE** | [RFC 7516](https://datatracker.ietf.org/doc/html/rfc7516) | Payload confidentiality (end-to-end encryption) |
| **JWK** | [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517) | JSON representation of cryptographic key material |
| **JWKS** | [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517) | Public key set distribution endpoint |

### Request Lifecycle

```
PSP Client                Gateway                  Backend
    │                        │                        │
    │  1. Build JSON payload  │                        │
    │  2. Encrypt → JWE       │                        │
    │  3. Sign    → JWS       │                        │
    │─────────── POST ───────►│                        │
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

---

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| Client Simulator | [Streamlit](https://streamlit.io) | Interactive PSP dashboard |
| API Gateway | [KrakenD](https://krakend.io) | Edge security / Policy Enforcement Point |
| Backend API | [FastAPI](https://fastapi.tiangolo.com) | Business logic processing |
| Key Management | [HashiCorp Vault](https://vaultproject.io) | Secrets and private key storage |
| JWKS Server | [Nginx](https://nginx.org) | Public key distribution |
| JOSE Library | [jwcrypto](https://jwcrypto.readthedocs.io) | JWS/JWE/JWK implementation |
| Infrastructure | [Docker Compose](https://docs.docker.com/compose/) | Local container orchestration |

---

## Project Structure

```
nfr-lab/
├── simulate_dashboard.py       # Streamlit PSP client simulator
├── setup_api_keys.py           # Cryptographic key generation script
├── docker-compose.yml          # Container orchestration (KrakenD, Vault, Nginx)
│
├── regulator_internal/
│   └── core_api.py             # FastAPI backend — decrypt JWE, process logic
│
├── psp_public/
│   └── bi_jwks.json            # JWKS file served by Nginx (public keys)
│
├── psp_private_jws.json        # PSP private key for JWS signing (lab only)
└── README.md
```

> ⚠️ **Note:** `psp_private_jws.json` should never be committed in a real environment. It is included here for lab simulation purposes only.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
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
pip install fastapi uvicorn jwcrypto streamlit watchdog requests pydantic
```

### 4. Generate Cryptographic Materials

This script generates JWK key pairs for PSP signing (JWS) and backend encryption (JWE), and writes the public key to the JWKS file.

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
- **Nginx** — JWKS endpoint on port `9090`

### 6. Initialize Vault and Load Keys

```bash
# Vault initialization and key seeding is handled by nfr-vault-init service
# Verify Vault is healthy:
docker compose logs vault
```

### 7. Run the Backend Service

```bash
python3 regulator_internal/core_api.py
```

Backend runs on `http://localhost:8000`.

### 8. Run the Client Dashboard

```bash
streamlit run simulate_dashboard.py --server.port 8501
```

Open `http://localhost:8501` in your browser.

---

## Usage

Once all services are running, use the Streamlit dashboard to:

1. **Build a fraud payload** — fill in sample PSP fraud event data
2. **Send a valid request** — payload is encrypted (JWE) and signed with a valid key (JWS), forwarded by the gateway to the backend
3. **Send a forged request** — payload is signed with an invalid key, rejected at the gateway before reaching the backend

---

## Simulation Scenarios

### ✅ Scenario 1: Valid PSP Request

Simulates a legitimate fraud event report from a registered PSP.

**Flow:**
1. Payload is serialized as JSON
2. Payload is encrypted using **JWE** (recipient: backend public key)
3. Request is signed using **JWS** (signer: valid PSP private key)
4. Gateway fetches public key from JWKS and validates JWS ✓
5. Validated request is forwarded to backend
6. Backend retrieves private key from Vault and decrypts JWE
7. Business logic executes, response returned

**Expected result:**
```
HTTP 200 OK
{
  "status": "Authorization Granted",
  "fraud_event": { ... }
}
```

---

### ❌ Scenario 2: Forged Signature

Simulates an attacker attempting to inject a fraudulent request using an unauthorized key.

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

# View logs
journalctl -u nfr-backend -f
```

---

## Security Notes

> This project is **intended for lab and demonstration purposes only.**

Before adapting this architecture for production, the following must be addressed:

| Area | Recommendation |
|---|---|
| **Audit Logging** | Centralized, tamper-evident audit log for all API events |
| **Secret Rotation** | Automated key rotation policy via Vault |
| **Rate Limiting** | Per-client rate limits at the gateway layer |
| **Mutual TLS (mTLS)** | Client certificate validation on top of JWS |
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
- [KrakenD Documentation](https://www.krakend.io/docs/)
- [HashiCorp Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [jwcrypto Documentation](https://jwcrypto.readthedocs.io/en/latest/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

---

<div align="center">

Built as a security architecture lab. Not for production use without proper hardening.

</div>
