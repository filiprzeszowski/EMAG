import os
import shutil
import zipfile
import requests
from tkinter import messagebox
from packaging.version import parse  # pip install packaging
import threading

# -------------------------------------------------------------------------
#                     SETTINGS / EXCLUSIONS
# -------------------------------------------------------------------------
# Folders or files to exclude from backup. 
# You might also exclude ".git", ".venv", etc. if they exist in your repo.
EXCLUDED_PATHS = {
    "backup",         # don't back up the backup folder itself
    "__pycache__",    # skip typical Python cache
    "venv",           # skip local Python environment
    ".git",           # skip git repo data
}

# -------------------------------------------------------------------------
#                 CHECK FOR UPDATES (GITHUB RELEASES)
# -------------------------------------------------------------------------
def check_for_updates(current_version):
    """
    Checks GitHub for the latest release tag on your repo
    and compares it with `current_version`.
    Return: (is_update_available, latest_version_str, zip_url)
    """
    try:
        url = "https://api.github.com/repos/filiprzeszowski/EMAG/releases/latest"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        release_info = response.json()

        latest_version = release_info["tag_name"]   # e.g. "1.2.3"
        update_url = release_info["zipball_url"]    # e.g. https://github.com/...zipball/...
        
        # Compare versions (pip install packaging)
        if parse(current_version) < parse(latest_version):
            return True, latest_version, update_url
        else:
            return False, None, None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return False, None, None


# -------------------------------------------------------------------------
#                    DOWNLOAD THE ZIPBALL
# -------------------------------------------------------------------------
def download_update(update_url, destination="update.zip"):
    """
    Downloads the zip file from update_url into `destination`.
    Returns the path of the downloaded file, or None on failure.
    """
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


# -------------------------------------------------------------------------
#                      INSTALL THE UPDATE
# -------------------------------------------------------------------------
def install_update(update_zip_path, extract_dir="update_temp"):
    """
    Installs the update by:
    1) Creating a backup of current files
    2) Extracting the new files into `extract_dir`
    3) Moving them into the current directory
    4) Cleaning up after success
    Returns True if successful, False otherwise.
    """
    try:
        backup_dir = "backup"
        os.makedirs(backup_dir, exist_ok=True)

        # 1) Backup current files
        for root, dirs, files in os.walk("."):
            # Skip excluded paths
            relative_root = os.path.relpath(root, ".")
            if any(x in relative_root for x in EXCLUDED_PATHS):
                continue

            for file in files:
                # Don't back up the update zip or any in excluded folders
                if file == os.path.basename(update_zip_path):
                    continue

                source = os.path.join(root, file)
                # Build the backup destination path
                dest = os.path.join(backup_dir, os.path.relpath(source, "."))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(source, dest)  # copy with metadata

        # 2) Extract update zip
        with zipfile.ZipFile(update_zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # 3) Move extracted files into our current directory
        # The GitHub zip typically contains a top-level folder like 
        # "filiprzeszowski-EMAG-<hash>/...", so we find that subfolder:
        subdirs = os.listdir(extract_dir)
        # If there's exactly one subfolder, we can assume it's the update
        # Otherwise, just move everything inside `extract_dir`.
        if len(subdirs) == 1 and os.path.isdir(os.path.join(extract_dir, subdirs[0])):
            update_root = os.path.join(extract_dir, subdirs[0])
        else:
            update_root = extract_dir

        for root, dirs, files in os.walk(update_root):
            relative_root = os.path.relpath(root, update_root)
            dest_root = os.path.join(".", relative_root)
            os.makedirs(dest_root, exist_ok=True)

            for file in files:
                source_path = os.path.join(root, file)
                destination_path = os.path.join(dest_root, file)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.move(source_path, destination_path)

        # 4) Cleanup
        os.remove(update_zip_path)
        shutil.rmtree(extract_dir)
        return True
    except Exception as e:
        print(f"Error installing update: {e}")
        return False


# -------------------------------------------------------------------------
#                       PERFORM UPDATE
# -------------------------------------------------------------------------
def perform_update(current_version):
    """
    Orchestrates the entire update process:
    1) Checks if there's a newer GitHub release
    2) If yes, asks user to confirm
    3) Downloads the update zip
    4) Installs it (with backup)
    5) Notifies user or reverts on failure
    """
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

    def update_thread():
        update_zip = download_update(update_url)
        if not update_zip:
            messagebox.showerror("Aktualizacja", "Nie udało się pobrać aktualizacji.")
            return

        success = install_update(update_zip)
        if success:
            messagebox.showinfo(
                "Aktualizacja",
                "Aktualizacja została pomyślnie zainstalowana. Uruchom ponownie aplikację."
            )
        else:
            messagebox.showerror(
                "Aktualizacja",
                "Wystąpił problem podczas instalacji aktualizacji. Przywracanie poprzedniej wersji..."
            )
            restore_backup()

    # Perform the download/install in a separate thread so the UI doesn't freeze.
    threading.Thread(target=update_thread, daemon=True).start()


# -------------------------------------------------------------------------
#                     RESTORE BACKUP ON FAILURE
# -------------------------------------------------------------------------
def restore_backup(backup_dir="backup"):
    """
    Restores files from `backup_dir` into the current directory if the update 
    installation fails. Then removes `backup_dir`.
    """
    try:
        for root, dirs, files in os.walk(backup_dir):
            relative_root = os.path.relpath(root, backup_dir)
            # Skip if path is in EXCLUDED_PATHS, although typically 
            # the backup wouldn't contain them anyway
            if any(x in relative_root for x in EXCLUDED_PATHS):
                continue

            for file in files:
                source_path = os.path.join(root, file)
                destination_path = os.path.join(".", relative_root, file)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.copy2(source_path, destination_path)

        shutil.rmtree(backup_dir)
        print("Backup restored successfully.")
    except Exception as e:
        print(f"Error restoring backup: {e}")
