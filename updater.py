import requests
import os
import sys
import shutil
import tempfile
import subprocess
from tkinter import messagebox

GITHUB_REPO = "SpritesDevelopments/Quantam-software"  # Replace with your GitHub repo

def get_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def download_file(url, dest):
    response = requests.get(url, stream=True)
    with open(dest, 'wb') as file:
        shutil.copyfileobj(response.raw, file)

def update_application():
    release = get_latest_release()
    if not release:
        messagebox.showerror("Error", "Failed to fetch the latest release.")
        return

    assets = release.get("assets", [])
    exe_asset = next((asset for asset in assets if asset["name"].endswith(".exe")), None)
    if not exe_asset:
        messagebox.showerror("Error", "No executable found in the latest release.")
        return

    exe_url = exe_asset["browser_download_url"]
    temp_dir = tempfile.mkdtemp()
    temp_exe_path = os.path.join(temp_dir, exe_asset["name"])

    try:
        download_file(exe_url, temp_exe_path)
        current_exe_path = sys.executable

        # Replace the current executable with the new one
        shutil.copy(temp_exe_path, current_exe_path)
        messagebox.showinfo("Success", "Application updated successfully. Restarting...")

        # Restart the application
        subprocess.Popen([current_exe_path])
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update application: {str(e)}")
    finally:
        shutil.rmtree(temp_dir)
