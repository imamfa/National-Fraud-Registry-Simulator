import os
import time
import requests
import gnupg
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

VAULT_URL = "http://127.0.0.1:8200/v1/secret/data/b2b/pgp"
VAULT_TOKEN = "root_token"
WATCH_DIR = "./sftp_data/psp_user/upload"
PROCESSED_DIR = "./sftp_data/psp_user/processed"
GPG_HOME = "./gpg_nfr_home"

os.makedirs(WATCH_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(GPG_HOME, mode=0o700, exist_ok=True)

gpg = gnupg.GPG(gnupghome=GPG_HOME)
gpg.encoding = 'utf-8'

def get_keys_from_vault():
    try:
        res = requests.get(VAULT_URL, headers={"X-Vault-Token": VAULT_TOKEN})
        res.raise_for_status()
        data = res.json()["data"]["data"]
        
        gpg.import_keys(data["regulator_private_key"])
        gpg.import_keys(data["psp_public_key"])
        return data["regulator_passphrase"]
    except Exception as e:
        print(f"[FATAL] Gagal menghubungi Vault: {e}")
        return None

class B2BFileHandler(FileSystemEventHandler):
    def __init__(self, passphrase):
        self.passphrase = passphrase

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.gpg'):
            time.sleep(2)
            self.process_file(event.src_path)

    def process_file(self, filepath):
        output_path = os.path.join(PROCESSED_DIR, os.path.basename(filepath).replace('.gpg', ''))
        with open(filepath, 'rb') as f:
            dec_status = gpg.decrypt_file(f, output=output_path, passphrase=self.passphrase, always_trust=True)

        if dec_status.ok and dec_status.valid:
            print(f"[SUCCESS] Decryption Passed! File: {output_path}")
            os.remove(filepath)
        else:
            print(f"[ERROR] Tampered File: {dec_status.status}")

if __name__ == "__main__":
    passphrase = get_keys_from_vault()
    if passphrase:
        event_handler = B2BFileHandler(passphrase)
        observer = Observer()
        observer.schedule(event_handler, path=WATCH_DIR, recursive=False)
        observer.start()
        print(f"[*] NFR Watchdog Active. Dropzone: {WATCH_DIR}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
