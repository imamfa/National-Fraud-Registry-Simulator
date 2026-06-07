from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jwcrypto import jwk, jwe
import uvicorn
import json

app = FastAPI(title="NFR Core API")

with open('regulator_private_jwe.json', 'r') as f:
    REGULATOR_PRIV_KEY = jwk.JWK.from_json(f.read())

class SecurePayload(BaseModel):
    encrypted_data: str

@app.post("/internal/process")
def process_data(payload: SecurePayload):
    try:
        jwetoken = jwe.JWE()
        jwetoken.deserialize(payload.encrypted_data)
        jwetoken.decrypt(REGULATOR_PRIV_KEY)
        
        data = json.loads(jwetoken.payload.decode('utf-8'))
        print(f"[ALERT] Report Received from {data.get('kode_psp')}: {data}")
        
        return {
            "status": "RECORDED",
            "message": "Report integrated into NFR Database.",
            "next_action": f"Initiating Broadcast Verification for Payment ID: {data.get('payment_id')}"
        }
    except Exception as e:
        print(f"[ERROR] Decryption Failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid Encrypted Payload")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="warning")
