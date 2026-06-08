from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jwcrypto import jwk, jwe
import uvicorn
import json

app = FastAPI(title="NFR Core API")

# Load Private Key untuk dekripsi JWE
try:
    with open('/home/ubuntu/nfr-lab/regulator_internal/regulator_private_jwe.json', 'r') as f:
        REGULATOR_PRIV_KEY = jwk.JWK.from_json(f.read())
except Exception as e:
    print(f"[FATAL] Gagal memuat JWE Private Key: {e}", flush=True)

class SecurePayload(BaseModel):
    encrypted_data: str

@app.post("/internal/process")
def process_data(payload: SecurePayload):
    try:
        # 1. Terima dan Dekripsi JWE
        jwetoken = jwe.JWE()
        jwetoken.deserialize(payload.encrypted_data)
        jwetoken.decrypt(REGULATOR_PRIV_KEY)
        
        # 2. Ekstrak data JSON murni
        data = json.loads(jwetoken.payload.decode('utf-8'))
        
        # 3. PRINT PAYLOAD KE LOG (flush=True agar langsung muncul di journalctl)
        print("="*50, flush=True)
        print(f"[SUCCESS] REQUEST DITERIMA DARI GATEWAY", flush=True)
        print(f"[PAYLOAD ASLI]:\n{json.dumps(data, indent=4)}", flush=True)
        print("="*50, flush=True)
        
        return {
            "status": "RECORDED",
            "message": "Report decrypted and processed securely.",
            "payment_id": data.get("payment_id")
        }
    except Exception as e:
        print(f"[ERROR] Dekripsi Gagal / Payload Tidak Valid: {e}", flush=True)
        raise HTTPException(status_code=400, detail="Invalid Encrypted Payload")

if __name__ == "__main__":
    # log_level="warning" menyembunyikan log akses HTTP 200 standar agar log kita lebih bersih
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="warning")
