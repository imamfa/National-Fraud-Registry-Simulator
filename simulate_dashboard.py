import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
import textwrap
import urllib.request
from jwcrypto import jwk, jwt, jwe

st.set_page_config(page_title="NFR API Simulator", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

try:
    PUBLIC_IP = urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode('utf-8')
except Exception:
    PUBLIC_IP = "127.0.0.1"

TARGET_URL = "http://127.0.0.1:8080/v1/sync"

def render_html(content: str):
    content = textwrap.dedent(content).strip()
    if hasattr(st, "html"):
        st.html(content)
    else:
        st.markdown(content, unsafe_allow_html=True)

st.markdown("""
<style>
    :root {
        color-scheme: dark !important;
        --bg-main: #020617;
        --bg-card: rgba(15, 23, 42, 0.86);
        --bg-card-soft: rgba(2, 6, 23, 0.62);
        --border-soft: rgba(148, 163, 184, 0.22);
        --border-blue: rgba(56, 189, 248, 0.34);
        --text-main: #e5e7eb;
        --text-soft: #cbd5e1;
        --text-muted: #94a3b8;
        --blue: #38bdf8;
        --blue-soft: rgba(14, 165, 233, 0.13);
        --green: #86efac;
        --red: #fca5a5;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, rgba(14, 165, 233, 0.14), transparent 30%), radial-gradient(circle at top right, rgba(99, 102, 241, 0.12), transparent 28%), linear-gradient(180deg, #020617 0%, #030712 100%) !important;
        color: var(--text-main) !important;
    }

    [data-testid="stHeader"] { background: transparent !important; }
    #MainMenu, footer { visibility: hidden !important; }
    [data-testid="collapsedControl"] { display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 999999 !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; max-width: 1320px !important; }
    h1, h2, h3, h4, h5, h6, p, li, label, span { color: var(--text-main); }
    small { color: var(--text-soft); }
    a { color: #7dd3fc !important; }
    hr { border-color: rgba(148, 163, 184, 0.18) !important; }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #020617 0%, #0f172a 100%) !important; border-right: 1px solid rgba(148, 163, 184, 0.18); }
    [data-testid="stSidebar"] * { color: var(--text-main); }
    [data-testid="stSidebar"] .stCaptionContainer, [data-testid="stSidebar"] small { color: var(--text-muted) !important; }
    [data-testid="stSidebarUserContent"] { padding-top: 1.45rem; }

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #0f172a !important; color: #e5e7eb !important; border: 1px solid rgba(148, 163, 184, 0.42) !important; border-radius: 10px !important; box-shadow: none !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: #38bdf8 !important; box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.14) !important; }
    .stSelectbox div[data-baseweb="select"] span, .stSelectbox div[data-baseweb="select"] svg { color: #e5e7eb !important; fill: #e5e7eb !important; }
    
    div[data-baseweb="popover"] { z-index: 999999 !important; }
    div[data-baseweb="popover"] > div, ul[role="listbox"] { background: #020617 !important; border: 1px solid rgba(56, 189, 248, 0.28) !important; border-radius: 12px !important; box-shadow: 0 20px 48px rgba(0, 0, 0, 0.55) !important; }

    .stButton > button { border-radius: 11px !important; font-weight: 800 !important; border: 1px solid rgba(148, 163, 184, 0.22) !important; transition: all 0.18s ease !important; }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 14px 28px rgba(0, 0, 0, 0.28); }

    .hero-card { width: 100%; margin-bottom: 18px; background: linear-gradient(135deg, rgba(15, 23, 42, 0.97), rgba(30, 41, 59, 0.86)), radial-gradient(circle at top right, rgba(56, 189, 248, 0.14), transparent 34%); border: 1px solid rgba(148, 163, 184, 0.24); border-radius: 24px; padding: 30px 32px; box-shadow: 0 24px 70px rgba(0, 0, 0, 0.30); }
    .hero-kicker { display: inline-flex; align-items: center; gap: 8px; padding: 5px 10px; border-radius: 999px; border: 1px solid rgba(56, 189, 248, 0.28); background: rgba(56, 189, 248, 0.10); color: #7dd3fc; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 12px; }
    .hero-title { margin: 0 0 12px 0; color: #f8fafc; font-size: clamp(2rem, 3.2vw, 2.55rem); line-height: 1.12; font-weight: 950; letter-spacing: -0.048em; }
    .hero-subtitle { max-width: 1080px; color: #cbd5e1; font-size: 0.96rem; line-height: 1.68; margin: 0; }

    .flow-wrap { margin: 0 0 24px 0; padding: 18px; border-radius: 22px; border: 1px solid var(--border-soft); background: radial-gradient(circle at top right, rgba(56, 189, 248, 0.10), transparent 30%), linear-gradient(180deg, rgba(15, 23, 42, 0.90), rgba(15, 23, 42, 0.70)); box-shadow: 0 18px 46px rgba(0, 0, 0, 0.22); }
    .flow-head { margin-bottom: 13px; }
    .flow-head h3 { margin: 0; color: #f8fafc; font-size: 1.2rem; font-weight: 950; letter-spacing: -0.02em; }
    .flow-head p { margin: 5px 0 0 0; color: var(--text-muted); font-size: 0.86rem; line-height: 1.45; }
    .flow-grid { display: grid; grid-template-columns: minmax(0, 1fr) 34px minmax(0, 1fr) 34px minmax(0, 1fr); gap: 9px; align-items: stretch; }
    .flow-node { min-height: 104px; border-radius: 16px; border: 1px solid var(--border-soft); background: linear-gradient(180deg, rgba(2, 6, 23, 0.74), rgba(15, 23, 42, 0.58)); padding: 13px; position: relative; overflow: hidden; }
    .flow-node::after { content: ""; position: absolute; top: -28px; right: -24px; width: 74px; height: 74px; border-radius: 999px; background: rgba(56, 189, 248, 0.08); }
    .flow-topline { display: flex; align-items: center; gap: 9px; margin-bottom: 8px; position: relative; z-index: 2; }
    .flow-step { display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 999px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.34); color: #7dd3fc; font-weight: 950; font-size: 0.75rem; flex-shrink: 0; }
    .flow-node h4 { margin: 0; color: #f8fafc; font-size: 0.92rem; font-weight: 950; position: relative; z-index: 2; }
    .flow-node p { margin: 0; color: #cbd5e1; line-height: 1.45; font-size: 0.82rem; position: relative; z-index: 2; }
    .flow-node b { color: #e0f2fe; }
    .flow-arrow { display: flex; align-items: center; justify-content: center; color: var(--blue); font-size: 1.5rem; font-weight: 950; opacity: 0.92; }
    .flow-note { margin-top: 10px; padding: 10px 12px; color: #cbd5e1; font-size: 0.82rem; line-height: 1.45; border-radius: 13px; background: rgba(2, 6, 23, 0.48); border: 1px solid rgba(148, 163, 184, 0.16); }

    .scenario-card { height: 100%; border-radius: 18px; padding: 18px; border: 1px solid rgba(148, 163, 184, 0.22); background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.66)); box-shadow: 0 16px 40px rgba(0, 0, 0, 0.20); }
    .scenario-card.valid { border-color: rgba(74, 222, 128, 0.28); }
    .scenario-card.invalid { border-color: rgba(248, 113, 113, 0.28); }
    .scenario-label { display: inline-flex; align-items: center; gap: 7px; padding: 5px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 900; margin-bottom: 10px; }
    .scenario-card.valid .scenario-label { color: var(--green); background: rgba(34, 197, 94, 0.14); border: 1px solid rgba(74, 222, 128, 0.30); }
    .scenario-card.invalid .scenario-label { color: var(--red); background: rgba(239, 68, 68, 0.14); border: 1px solid rgba(248, 113, 113, 0.30); }
    .scenario-card h4 { margin: 0 0 8px 0; color: #f8fafc; font-weight: 950; font-size: 1.05rem; }
    .scenario-card p { margin: 0; color: #cbd5e1; line-height: 1.55; font-size: 0.92rem; }

    .stack-board { width: 100%; margin: 14px 0 26px 0; border-radius: 22px; padding: 24px; background: radial-gradient(circle at top right, rgba(56, 189, 248, 0.10), transparent 32%), linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.66)); border: 1px solid var(--border-soft); box-shadow: 0 18px 46px rgba(0, 0, 0, 0.24); }
    .stack-head { margin-bottom: 18px; }
    .stack-head h3 { margin: 0; color: #f8fafc; font-size: 1.22rem; font-weight: 950; letter-spacing: -0.02em; }
    .stack-head p { margin: 6px 0 0 0; color: var(--text-muted); font-size: 0.86rem; line-height: 1.5; }
    .stack-list { display: flex; flex-direction: column; gap: 12px; }
    .stack-card { width: 100%; border-radius: 18px; border: 1px solid var(--border-soft); background: linear-gradient(180deg, rgba(2, 6, 23, 0.76), rgba(15, 23, 42, 0.58)); padding: 16px 18px; position: relative; overflow: hidden; transition: all 0.18s ease; }
    .stack-card::after { content: ""; position: absolute; top: -34px; right: -28px; width: 96px; height: 96px; border-radius: 999px; background: rgba(56, 189, 248, 0.08); pointer-events: none; }
    .stack-card.has-access:hover { transform: translateY(-1px); border-color: rgba(56, 189, 248, 0.42); background: radial-gradient(circle at top right, rgba(56, 189, 248, 0.12), transparent 38%), rgba(15, 23, 42, 0.98); box-shadow: 0 18px 44px rgba(0, 0, 0, 0.30); }
    .stack-front { display: grid; grid-template-columns: 58px minmax(0, 1fr); gap: 14px; align-items: center; position: relative; z-index: 2; }
    .stack-icon { width: 52px; height: 52px; border-radius: 16px; display: inline-flex; align-items: center; justify-content: center; background: rgba(56, 189, 248, 0.13); border: 1px solid rgba(56, 189, 248, 0.26); font-size: 1.45rem; }
    .stack-main { min-width: 0; }
    .stack-title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
    .stack-title { color: #f8fafc; font-size: 1rem; font-weight: 950; }
    .stack-type { color: #93c5fd; background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.22); border-radius: 999px; padding: 3px 8px; font-size: 0.68rem; font-weight: 850; }
    .stack-desc { color: #cbd5e1; font-size: 0.86rem; line-height: 1.5; max-width: 96%; }
    .access-hint, .no-access-note { margin-top: 7px; font-size: 0.76rem; font-weight: 850; }
    .access-hint { color: #7dd3fc; }
    .no-access-note { color: #64748b; }
    .access-panel { position: relative; z-index: 2; margin-left: 72px; max-height: 0; opacity: 0; overflow: hidden; transform: translateY(-4px); transition: max-height 0.22s ease, opacity 0.18s ease, transform 0.18s ease, margin-top 0.18s ease; }
    .stack-card.has-access:hover .access-panel { max-height: 180px; opacity: 1; transform: translateY(0); margin-top: 12px; }
    .access-title { color: var(--blue); font-size: 0.84rem; font-weight: 950; margin-bottom: 7px; }
    .copy-list { display: grid; grid-template-columns: repeat(3, minmax(160px, 1fr)); gap: 8px; }
    .copy-item { min-width: 0; background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 10px; padding: 8px 9px; }
    .copy-label { color: #94a3b8; font-size: 0.68rem; font-weight: 850; margin-bottom: 4px; }
    .copy-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 8px; }
    .copy-value { min-width: 0; color: #bae6fd; font-family: Consolas, "Fira Code", monospace; font-size: 0.73rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; user-select: text; }
    .copy-btn { border: 1px solid rgba(56, 189, 248, 0.34); background: rgba(14, 165, 233, 0.13); color: #bae6fd; border-radius: 8px; padding: 5px 8px; font-size: 0.68rem; font-weight: 900; cursor: pointer; transition: all 0.16s ease; white-space: nowrap; }
    .copy-btn:hover { background: rgba(14, 165, 233, 0.24); transform: translateY(-1px); }

    .glass-card { background: linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.78)); border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 18px; padding: 24px; margin-bottom: 20px; box-shadow: 0 18px 46px rgba(0, 0, 0, 0.26); color: #e5e7eb; }
    .title-text { font-weight: 900; font-size: 1.24rem; margin-bottom: 15px; border-bottom: 1px solid rgba(148, 163, 184, 0.22); padding-bottom: 10px; color: #f8fafc; letter-spacing: -0.02em; }
    .section-chip { display: inline-flex; align-items: center; gap: 7px; padding: 5px 10px; border-radius: 999px; color: #bae6fd; background: rgba(14, 165, 233, 0.13); border: 1px solid rgba(56, 189, 248, 0.26); font-size: 0.78rem; font-weight: 800; margin-bottom: 10px; }
    .terminal-box { background-color: #020617; color: #d4d4d4; font-family: 'Consolas', 'Fira Code', monospace; font-size: 0.85rem; padding: 15px; border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.22); overflow-x: auto; margin: 10px 0 20px 0; }
    .hl-cyan { color: #67e8f9; } .hl-emerald { color: #86efac; font-weight: bold; } .hl-rose { color: #fda4af; font-weight: bold; }
    .badge-pass { background: rgba(34, 197, 94, 0.16); color: #86efac; border: 1px solid rgba(74, 222, 128, 0.55); padding: 12px 16px; border-radius: 12px; font-weight: 900; margin: 15px 0; text-align: center; }
    .badge-fail { background: rgba(239, 68, 68, 0.16); color: #fca5a5; border: 1px solid rgba(248, 113, 113, 0.55); padding: 12px 16px; border-radius: 12px; font-weight: 900; margin: 15px 0; text-align: center; }
    [data-testid="stJson"] { background: #020617 !important; border-radius: 12px !important; border: 1px solid rgba(148, 163, 184, 0.18) !important; }
    [data-testid="stAlert"] { border-radius: 14px !important; border: 1px solid rgba(148, 163, 184, 0.18) !important; }

    @media (max-width: 1050px) { .flow-grid { grid-template-columns: 1fr; } .flow-arrow { transform: rotate(90deg); min-height: 26px; } .copy-list { grid-template-columns: 1fr; } }
    @media (max-width: 720px) { .hero-card { padding: 24px; } .stack-front { grid-template-columns: 1fr; } .access-panel { margin-left: 0; } .stack-icon { width: 48px; height: 48px; } }
    .section-heading { margin: 4px 0 14px 0; }
    .section-heading .section-title { display: inline-flex; align-items: center; gap: 8px; color: #f8fafc; font-size: 1.08rem; font-weight: 950; letter-spacing: -0.02em; }
    .section-heading .section-mark { width: 9px; height: 9px; border-radius: 999px; background: #38bdf8; box-shadow: 0 0 18px rgba(56, 189, 248, 0.65); display: inline-block; }
    .section-heading .section-subtitle { margin-top: 4px; color: #94a3b8; font-size: 0.82rem; line-height: 1.45; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
render_html(f"""<div class="hero-card">
    <div class="hero-kicker">🛡️ API Security Simulator</div>
    <h1 class="hero-title">National Fraud Registry Simulator</h1>
    <p class="hero-subtitle">
        Simulator ini mendemonstrasikan pengamanan pertukaran data API skala Enterprise.
        Arsitektur lab memisahkan fungsi <b>Edge Security</b> pada API Gateway dari proses
        <b>Backend Application</b>, dengan pendekatan <b>JOSE</b>: <b>JWS</b> untuk authentication,
        <b>JWE</b> untuk payload confidentiality, serta <b>JWK/JWKS</b> untuk public key distribution.
    </p>
</div>""")

# --- FLOW ---
render_html("""<div class="flow-wrap">
    <div class="flow-head">
        <h3>🧭 Alur Pengamanan Transmisi API</h3>
        <p>Ringkasan proses yang disimulasikan.</p>
    </div>
    <div class="flow-grid">
        <div class="flow-node">
            <div class="flow-topline"><div class="flow-step">1</div><h4>Confidentiality</h4></div>
            <p>Payload dibungkus dengan <b>JWE</b>, sehingga data sensitif tidak terbaca selama transmisi.</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-node">
            <div class="flow-topline"><div class="flow-step">2</div><h4>Authentication</h4></div>
            <p>Identitas pengirim dibuktikan dengan <b>JWS</b>. Gateway memverifikasi signature menggunakan <b>JWKS</b>.</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-node">
            <div class="flow-topline"><div class="flow-step">3</div><h4>Backend Isolation</h4></div>
            <p>Request tidak valid ditolak di perimeter. Backend hanya menerima traffic yang sudah lolos validasi.</p>
        </div>
    </div>
    <div class="flow-note">API Gateway menangani validasi awal di edge, sedangkan backend fokus pada dekripsi JWE dan business logic.</div>
</div>""")

@st.cache_resource
def load_crypto_materials():
    try:
        with open('psp_private_jws.json', 'r') as f:
            psp_priv = jwk.JWK.from_json(f.read())
        with open('psp_public/regulator_jwks.json', 'r') as f:
            reg_pub = jwk.JWK.from_json(json.dumps(json.load(f)["keys"][0]))
        return psp_priv, reg_pub
    except Exception:
        return None, None

psp_priv_key, regulator_pub_key = load_crypto_materials()

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.markdown("### 📝 Fraud Suspect Form")
    st.caption("Input parameter payload untuk transmisi B2B.")

    kode_psp = st.text_input("Kode PSP Pengirim", "PSP-BANK-001")
    payment_id = st.text_input("Payment ID Terlapor", "PAY-CIF8829-2026")
    no_rekening = st.text_input("Nomor Rekening", "081234567890")
    status_fraud = st.selectbox("Klasifikasi Indikasi", ["SUSPECTED_FRAUD", "CONFIRMED_FRAUD", "MERCHANT_BLACKLIST"])
    indikasi = st.text_area("Analisis / Keterangan", "High-velocity chained transactions detected.")

    st.divider()
    btn_legit = st.button("🚀 Transmit Valid Payload", type="primary", use_container_width=True)
    btn_attack = st.button("☠️ Inject Forged Signature", use_container_width=True)

if not psp_priv_key:
    st.error("Material kriptografi belum digenerate.")
    st.stop()

# --- INITIAL EMPTY STATE ---
if not (btn_legit or btn_attack):
    st.markdown('<div class="section-heading"><div class="section-title"><span class="section-mark"></span>Skenario Simulasi</div><div class="section-subtitle">Dua skenario utama untuk membuktikan kontrol keamanan pada API Gateway.</div></div>', unsafe_allow_html=True)
    scen_col1, scen_col2 = st.columns(2)
    with scen_col1:
        render_html("""<div class="scenario-card valid"><div class="scenario-label">✅ Skenario Sah</div><h4>Transmit Valid Payload</h4><p>Client mengirim payload JWE dan menambahkan JWS dengan private key PSP valid. Gateway memverifikasi signature, lalu request diteruskan ke backend.</p></div>""")
    with scen_col2:
        render_html("""<div class="scenario-card invalid"><div class="scenario-label">⛔ Skenario Tidak Sah</div><h4>Inject Forged Signature</h4><p>Request seolah berasal dari PSP, tetapi ditandatangani dengan private key palsu. Gateway menolak request di perimeter sebelum menyentuh backend.</p></div>""")
    st.markdown("---")

    render_html(f"""<div class="stack-board">
    <div class="stack-head">
        <h3>🛠️ Technology Stack & Komponen Lab</h3>
        <p>Komponen lab disusun sesuai perannya dalam arsitektur <b>JOSE-based API security</b>.</p>
    </div>
    <div class="stack-list">
        <div class="stack-card has-access">
            <div class="stack-front">
                <div class="stack-icon">🖥️</div>
                <div class="stack-main">
                    <div class="stack-title-row"><div class="stack-title">Streamlit Dashboard</div><div class="stack-type">Interactive Client Simulator</div></div>
                    <div class="stack-desc">Dashboard untuk menjalankan simulasi, membentuk JWE, membuat JWS, dan mengirim HTTP request.</div>
                    <div class="access-hint">Hover untuk akses dashboard</div>
                </div>
            </div>
            <div class="access-panel">
                <div class="access-title">Detail Akses</div>
                <div class="copy-list">
                    <div class="copy-item"><div class="copy-label">Dashboard URL</div><div class="copy-row"><div class="copy-value">http://{PUBLIC_IP}:8501</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                </div>
            </div>
        </div>

        <div class="stack-card has-access">
            <div class="stack-front">
                <div class="stack-icon">🛡️</div>
                <div class="stack-main">
                    <div class="stack-title-row"><div class="stack-title">KrakenD API Gateway</div><div class="stack-type">Edge Security</div></div>
                    <div class="stack-desc">Edge Security layer yang memvalidasi JWS sebelum request diteruskan ke Backend.</div>
                    <div class="access-hint">Hover untuk detail akses</div>
                </div>
            </div>
            <div class="access-panel">
                <div class="access-title">Detail Akses</div>
                <div class="copy-list">
                    <div class="copy-item"><div class="copy-label">Endpoint</div><div class="copy-row"><div class="copy-value">http://{PUBLIC_IP}:8080/v1/sync</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                    <div class="copy-item"><div class="copy-label">Method</div><div class="copy-row"><div class="copy-value">POST</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                    <div class="copy-item"><div class="copy-label">Requirement</div><div class="copy-row"><div class="copy-value">Header JWS + Body JSON JWE</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                </div>
            </div>
        </div>

        <div class="stack-card">
            <div class="stack-front">
                <div class="stack-icon">🏦</div>
                <div class="stack-main">
                    <div class="stack-title-row"><div class="stack-title">Backend Application</div><div class="stack-type">FastAPI Core Service</div></div>
                    <div class="stack-desc">Backend Application yang menerima request valid, mendekripsi JWE, lalu menjalankan business logic.</div>
                    <div class="no-access-note">Internal service, tidak dibuka sebagai akses publik.</div>
                </div>
            </div>
        </div>

        <div class="stack-card has-access">
            <div class="stack-front">
                <div class="stack-icon">🔐</div>
                <div class="stack-main">
                    <div class="stack-title-row"><div class="stack-title">HashiCorp Vault</div><div class="stack-type">KMS & Secret Store</div></div>
                    <div class="stack-desc">KMS dan Secret Store untuk menjaga private key backend tetap terpisah dari application code.</div>
                    <div class="access-hint">Hover untuk detail akses</div>
                </div>
            </div>
            <div class="access-panel">
                <div class="access-title">Detail Akses</div>
                <div class="copy-list">
                    <div class="copy-item"><div class="copy-label">Vault URL</div><div class="copy-row"><div class="copy-value">http://{PUBLIC_IP}:8200</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                    <div class="copy-item"><div class="copy-label">Token</div><div class="copy-row"><div class="copy-value">root_token</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                </div>
            </div>
        </div>

        <div class="stack-card has-access">
            <div class="stack-front">
                <div class="stack-icon">🌐</div>
                <div class="stack-main">
                    <div class="stack-title-row"><div class="stack-title">Nginx Public JWKS Endpoint</div><div class="stack-type">Public Key Distribution</div></div>
                    <div class="stack-desc">Nginx menyajikan JWKS berisi public key PSP yang digunakan gateway untuk signature verification.</div>
                    <div class="access-hint">Hover untuk detail akses</div>
                </div>
            </div>
            <div class="access-panel">
                <div class="access-title">Detail Akses</div>
                <div class="copy-list">
                    <div class="copy-item"><div class="copy-label">JWKS URL</div><div class="copy-row"><div class="copy-value">http://{PUBLIC_IP}:8081/jwks.json</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                </div>
            </div>
        </div>

        <div class="stack-card has-access">
            <div class="stack-front">
                <div class="stack-icon">📁</div>
                <div class="stack-main">
                    <div class="stack-title-row"><div class="stack-title">SFTP Dropzone & Watchdog</div><div class="stack-type">Batch Processing</div></div>
                    <div class="stack-desc">Menerima file terenkripsi GPG secara batch dan memprosesnya secara real-time menggunakan Python PollingObserver.</div>
                    <div class="access-hint">Hover untuk detail akses</div>
                </div>
            </div>
            <div class="access-panel">
                <div class="access-title">Detail Akses</div>
                <div class="copy-list">
                    <div class="copy-item"><div class="copy-label">SFTP URL</div><div class="copy-row"><div class="copy-value">sftp://{PUBLIC_IP}:2222</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                    <div class="copy-item"><div class="copy-label">Kredensial</div><div class="copy-row"><div class="copy-value">psp_user : password_psp_123</div><button class="copy-btn" type="button" onclick="var t=this.parentElement.querySelector('.copy-value').innerText;if(navigator.clipboard){{navigator.clipboard.writeText(t);}}else{{var e=document.createElement('textarea');e.value=t;document.body.appendChild(e);e.select();document.execCommand('copy');document.body.removeChild(e);}}this.innerText='Copied';setTimeout(()=>this.innerText='Copy',900);">Copy</button></div></div>
                </div>
            </div>
        </div>
    </div>
</div>""")

# --- TRAFFIC EXECUTION STATE ---
if btn_legit or btn_attack:
    payload_dict = {"kode_psp": kode_psp, "payment_id": payment_id, "nomor_rekening": no_rekening, "status_fraud": status_fraud, "indikasi": indikasi}
    raw_payload_bytes = json.dumps(payload_dict).encode('utf-8')

    col_client, col_server = st.columns([1, 1])

    with col_client:
        st.markdown('<div class="section-chip">💻 PSP Client Edge</div>', unsafe_allow_html=True)
        st.markdown('<div class="title-text">Payload Preparation</div>', unsafe_allow_html=True)
        st.markdown("<b>1. Cleartext JSON Payload</b>", unsafe_allow_html=True)
        st.json(payload_dict)
        st.markdown("<b>2. Hybrid Encryption (JWE Generation)</b>", unsafe_allow_html=True)
        st.markdown("<small>Data dienkripsi menggunakan <span class='hl-cyan'>Content Encryption Key AES-256-GCM</span>. Kunci ini kemudian dibungkus menggunakan <b>Public Key RSA</b> milik Regulator dengan <span class='hl-cyan'>RSA-OAEP-256</span>.</small>", unsafe_allow_html=True)

        jwetoken = jwe.JWE(plaintext=raw_payload_bytes, protected={"alg": "RSA-OAEP-256", "enc": "A256GCM"})
        jwetoken.add_recipient(regulator_pub_key)
        encrypted_body = jwetoken.serialize(compact=True)
        st.markdown(f'<div class="terminal-box">{encrypted_body[:85]}...</div>', unsafe_allow_html=True)

        st.markdown("<b>3. Authentication Signature (JWS Header)</b>", unsafe_allow_html=True)
        if btn_legit:
            st.markdown("<small>Header ditandatangani menggunakan <span class='hl-emerald'>Private Key Valid</span> milik PSP.</small>", unsafe_allow_html=True)
            jwstoken = jwt.JWT(header={"alg": "RS256", "kid": "psp-jws-prod"}, claims={"iss": kode_psp, "action": "submit_fraud"})
            jwstoken.make_signed_token(psp_priv_key)
            final_header = jwstoken.serialize()
            st.markdown(f'<div class="terminal-box">Authorization: Bearer <span class="hl-emerald">{final_header[:50]}...</span></div>', unsafe_allow_html=True)
        else:
            st.markdown("<small>Simulasi attacker: request menggunakan <span class='hl-rose'>private key palsu</span>.</small>", unsafe_allow_html=True)
            fake_key = jwk.JWK.generate(kty='RSA', size=2048)
            jwstoken = jwt.JWT(header={"alg": "RS256", "kid": "psp-jws-prod"}, claims={"iss": "attacker_node", "action": "submit_fraud"})
            jwstoken.make_signed_token(fake_key)
            final_header = jwstoken.serialize()
            st.markdown(f'<div class="terminal-box">Authorization: Bearer <span class="hl-rose">{final_header[:50]}... [FORGED]</span></div>', unsafe_allow_html=True)

    with col_server:
        st.markdown('<div class="section-chip">🏦 Backend Regulator</div>', unsafe_allow_html=True)
        st.markdown('<div class="title-text">Gateway Enforcement Result</div>', unsafe_allow_html=True)

        with st.spinner("Transmitting data through DMZ..."):
            time.sleep(1.2)
            headers = {"Authorization": f"Bearer {final_header}"}
            json_body = {"encrypted_data": encrypted_body}

            try:
                res = requests.post(TARGET_URL, headers=headers, json=json_body)
                if res.status_code == 200:
                    st.markdown('<div class="badge-pass">✅ AUTHORIZATION GRANTED (HTTP 200)</div>', unsafe_allow_html=True)
                    st.markdown("<small>KrakenD memvalidasi JWS via endpoint JWKS. <b>Akses diloloskan.</b></small>", unsafe_allow_html=True)
                    st.markdown("<br><b>4. Core System Decryption (Vault Integration)</b>", unsafe_allow_html=True)
                    st.markdown("<small>Backend mendekripsi JWE menggunakan private key dari Vault dan menjalankan business logic.</small>", unsafe_allow_html=True)
                    st.json(res.json())
                else:
                    st.markdown(f'<div class="badge-fail">⛔ ACCESS DENIED (HTTP {res.status_code})</div>', unsafe_allow_html=True)
                    st.markdown("<small>KrakenD mendeteksi signature tidak valid. Public key di JWKS tidak cocok dengan signature request.</small>", unsafe_allow_html=True)
                    st.markdown("<br><b>🛡️ Security Perimeter Status</b>", unsafe_allow_html=True)
                    st.error("Request ditolak oleh API Gateway. Backend tidak perlu memproses traffic tidak sah.")
            except requests.exceptions.ConnectionError:
                st.error("Gagal terhubung ke KrakenD Gateway. Periksa status Docker Container.")

# --- HACK: BYPASS STREAMLIT DOMPURIFY ONCLICK STRIPPING ---
components.html("""
<script>
const parentDoc = window.parent.document;
// Cegah script berjalan berulang kali saat Streamlit re-render
if (!parentDoc.getElementById('nfr-copy-hack')) {
    const marker = parentDoc.createElement('div');
    marker.id = 'nfr-copy-hack';
    marker.style.display = 'none';
    parentDoc.body.appendChild(marker);

    parentDoc.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('copy-btn')) {
            const val = e.target.parentElement.querySelector('.copy-value').innerText;
            const el = parentDoc.createElement('textarea');
            el.value = val;
            parentDoc.body.appendChild(el);
            el.select();
            parentDoc.execCommand('copy');
            parentDoc.body.removeChild(el);
            
            e.target.innerText = 'Copied!';
            setTimeout(() => e.target.innerText = 'Copy', 1200);
        }
    });
}
</script>
""", height=0, width=0)
