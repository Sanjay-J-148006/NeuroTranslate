import os
import sys

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("Error: huggingface_hub is not installed.")
    print("Please install it first by running: pip install huggingface_hub")
    sys.exit(1)

# Helper to read HF_TOKEN from .env file
def get_env_token():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("HF_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    # Remove surrounding quotes if present
                    if token.startswith(('"', "'")) and token.endswith(('"', "'")):
                        token = token[1:-1]
                    # Check if it's the placeholder
                    if "token" not in token.lower() and len(token) > 10:
                        return token
    return None

print("=================================================================")
print(" NeuroTranslate — IndicTrans2 Offline Downloader")
print("=================================================================")

# Load token dynamically from .env or prompt user (no hardcoded secrets!)
HF_TOKEN = get_env_token()

if HF_TOKEN:
    print("Detected Hugging Face token in local .env file.")
else:
    print("No valid token detected in local .env file.")
    print("Please paste your Hugging Face User Access Token (Read role) below.")
    print("Create a token at: https://huggingface.co/settings/tokens")
    HF_TOKEN = input("Enter HF Token: ").strip()

if not HF_TOKEN or len(HF_TOKEN) < 10:
    print("Error: A valid Hugging Face token is required to download this model.")
    sys.exit(1)

REPO_ID = "ai4bharat/indictrans2-indic-en-dist-200M"
local_dir = os.path.abspath("./indictrans2-model")

print("-----------------------------------------------------------------")
print(f"Target Model: {REPO_ID}")
print(f"Destination:  {local_dir}")
print("Starting download (this might take a few minutes)...")
print("-----------------------------------------------------------------")

try:
    model_path = snapshot_download(
        repo_id=REPO_ID,
        token=HF_TOKEN,
        local_dir=local_dir,
        local_dir_use_symlinks=False
    )
    print("\n🎉 DOWNLOAD COMPLETE!")
    print("=================================================================")
    print(f"All files successfully downloaded to: {model_path}")
    print("=================================================================")
    print("Steps to copy this model to your offline machine:")
    print("1. Copy the 'indictrans2-model' folder to a USB drive.")
    print("2. On your offline machine, open this directory:")
    print("   C:\\Users\\HP\\.cache\\huggingface\\hub\\")
    print("3. Create a folder named: models--ai4bharat--indictrans2-indic-en-dist-200M")
    print("4. Inside it, create a folder named: snapshots")
    print("5. Inside 'snapshots', create a folder named: main")
    print("6. Paste all contents of 'indictrans2-model' inside that 'main' folder.")
    print("=================================================================")
except Exception as e:
    print(f"\n❌ Download failed: {e}")
    print("\nEnsure you have:")
    print("1. Passed a valid token.")
    print("2. Accepted the model repository terms of service at:")
    print(f"   https://huggingface.co/{REPO_ID}")
