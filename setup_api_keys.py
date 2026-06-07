import json
from jwcrypto import jwk

print("[*] Generating API Keys (JOSE)...")

reg_key = jwk.JWK.generate(kty='RSA', size=2048, kid='regulator-jwe-prod', alg='RSA-OAEP-256', use='enc')
with open('regulator_internal/regulator_private_jwe.json', 'w') as f:
    f.write(reg_key.export_private())
with open('psp_public/regulator_jwks.json', 'w') as f:
    json.dump({"keys": [json.loads(reg_key.export_public())]}, f, indent=2)

psp_key = jwk.JWK.generate(kty='RSA', size=2048, kid='psp-jws-prod', alg='RS256', use='sig')
with open('psp_private_jws.json', 'w') as f:
    f.write(psp_key.export_private())
with open('psp_public/jwks.json', 'w') as f:
    json.dump({"keys": [json.loads(psp_key.export_public())]}, f, indent=2)

print("[+] Keys berhasil di-generate.")
