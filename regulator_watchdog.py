import os
import time
import requests
import gnupg
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

# Menggunakan Absolute Path agar stabil saat dijalankan systemd
BASE_DIR = "/home/ubuntu/nfr-lab"
VAULT_URL = "http://127.0.0.1:8200/v1/secret/data/b2b/pgp"
VAULT_TOKEN = "root_token"
WATCH_DIR = os.path.join(BASE_DIR, "sftp_data/psp_user/upload")
PROCESSED_DIR = os.path.join(BASE_DIR, "sftp_data/psp_user/processed")
GPG_HOME = os.path.join(BASE_DIR, "gpg_nfr_home")

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
        print(f"[FATAL] Gagal menghubungi Vault: {e}", flush=True)
        return None

class B2BFileHandler(FileSystemEventHandler):
    def __init__(self, passphrase):
        self.passphrase = passphrase

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.gpg'):
            print(f"\n[EVENT] File .gpg baru tertangkap di Dropzone: {event.src_path}", flush=True)
            # Beri jeda agar SFTP selesai menulis file secara penuh
            time.sleep(3)
            self.process_file(event.src_path)

    def process_file(self, filepath):
        try:
            print(f"[*] Memulai dekripsi dan verifikasi PGP Envelope...", flush=True)
            output_path = os.path.join(PROCESSED_DIR, os.path.basename(filepath).replace('.gpg', ''))
            
            with open(filepath, 'rb') as f:
                dec_status = gpg.decrypt_file(f, output=output_path, passphrase=self.passphrase, always_trust=True)

            if dec_status.ok and dec_status.valid:
                print(f"[SUCCESS] Dekripsi & Verifikasi Tanda Tangan Valid! File aman di: {output_path}", flush=True)
                os.remove(filepath)
            else:
                print(f"[ERROR] Akses Ditolak / File Dimanipulasi! Status: {dec_status.status} | Detail: {dec_status.stderr}", flush=True)
        except Exception as e:
            print(f"[EXCEPTION] Sistem crash saat memproses file: {e}", flush=True)

if __name__ == "__main__":
    print("[*] Inisialisasi Sistem Watchdog NFR...", flush=True)
    passphrase = get_keys_from_vault()
    
    if passphrase:
        event_handler = B2BFileHandler(passphrase)
        # Mengganti ke PollingObserver (Sangat tangguh untuk Docker Volume Bind Mounts)
        observer = PollingObserver(timeout=2.0)
        observer.schedule(event_handler, path=WATCH_DIR, recursive=False)
        observer.start()
        print(f"[*] NFR Watchdog PollingObserver ACTIVE. Dropzone: {WATCH_DIR}", flush=True)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        print("[FATAL] Skrip dimatikan karena gagal mengekstrak kunci dari Vault.", flush=True)
