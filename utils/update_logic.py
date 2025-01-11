import os
import shutil
import zipfile
import requests
from tkinter import messagebox
from packaging.version import parse  # Install with `pip install packaging`
import threading

def check_for_updates(current_version):
    """Check for application updates."""
    try:
        response = requests.get("https://api.github.com/repos/filiprzeszowski/EMAG/releases/latest", timeout=10)
        response.raise_for_status()
        release_info = response.json()
        latest_version = release_info["tag_name"]
        update_url = release_info["zipball_url"]

        # Compare versions
        if parse(current_version) < parse(latest_version):
            return True, latest_version, update_url
        return False, None, None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return False, None, None


def download_update(update_url, destination="update.zip"):
    """Download the update zip file."""
    try:
        with requests.get(update_url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(destination, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        return destination
    except Exception as e:
        print(f"Error downloading update: {e}")
        return None


def install_update(update_zip_path, extract_dir="update_temp"):
    """Install the update by replacing files."""
    try:
        # Backup current files
        backup_dir = "backup"
        os.makedirs(backup_dir, exist_ok=True)
        for root, dirs, files in os.walk("."):
            for file in files:
                if file != update_zip_path:
                    source = os.path.join(root, file)
                    dest = os.path.join(backup_dir, os.path.relpath(source, "."))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(source, dest)

        # Extract update zip
        with zipfile.ZipFile(update_zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Copy new files to application directory
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                source_path = os.path.join(root, file)
                relative_path = os.path.relpath(source_path, extract_dir)
                destination_path = os.path.join(".", relative_path)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.move(source_path, destination_path)

        # Clean up
        os.remove(update_zip_path)
        shutil.rmtree(extract_dir)
        return True
    except Exception as e:
        print(f"Error installing update: {e}")
        return False


def perform_update(current_version):
    """Perform the update process."""
    is_update_available, latest_version, update_url = check_for_updates(current_version)

    if not is_update_available:
        messagebox.showinfo("Aktualizacja", "Masz najnowszą wersję aplikacji.")
        return

    confirm = messagebox.askyesno(
        "Aktualizacja",
        f"Dostępna jest nowa wersja ({latest_version}). Czy chcesz zaktualizować?"
    )
    if not confirm:
        return

    # Download update
    def update_thread():
        update_zip = download_update(update_url)
        if not update_zip:
            messagebox.showerror("Aktualizacja", "Nie udało się pobrać aktualizacji.")
            return

        # Install update
        success = install_update(update_zip)
        if success:
            messagebox.showinfo(
                "Aktualizacja",
                "Aktualizacja została pomyślnie zainstalowana. Uruchom ponownie aplikację."
            )
        else:
            messagebox.showerror(
                "Aktualizacja",
                "Wystąpił problem podczas instalacji aktualizacji. Przywracanie poprzedniej wersji."
            )
            restore_backup()

    threading.Thread(target=update_thread, daemon=True).start()


def restore_backup(backup_dir="backup"):
    """Restore files from backup in case of update failure."""
    try:
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                source_path = os.path.join(root, file)
                relative_path = os.path.relpath(source_path, backup_dir)
                destination_path = os.path.join(".", relative_path)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.copy2(source_path, destination_path)
        shutil.rmtree(backup_dir)
        print("Backup restored successfully.")
    except Exception as e:
        print(f"Error restoring backup: {e}")
