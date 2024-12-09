from gui.app_window import run_gui

if __name__ == "__main__":
    try:
        run_gui()
    except Exception as e:
        input(f"An error occurred: {e}\nPress Enter to exit...")