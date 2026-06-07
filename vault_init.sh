#!/bin/bash
sleep 10
REGULATOR_PRIV_JSON=$(jq -Rs . < /home/ubuntu/nfr-lab/regulator_priv.asc)
PSP_PUB_JSON=$(jq -Rs . < /home/ubuntu/nfr-lab/psp_pub.asc)

curl -s -H "X-Vault-Token: root_token" \
     -X POST \
     -H "Content-Type: application/json" \
     -d "{
           \"data\": {
             \"regulator_private_key\": $REGULATOR_PRIV_JSON,
             \"regulator_passphrase\": \"password_regulator_123\",
             \"psp_public_key\": $PSP_PUB_JSON
           }
         }" \
     http://127.0.0.1:8200/v1/secret/data/b2b/pgp

echo "Vault Initialization Complete"
