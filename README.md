# ChirPet

A cute, interactive desktop pet written in Python with PyQt6.

## Installation

1.  Install Python 3.x.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running

```bash
python main.py
```

## Building the Executable

To build a standalone `.exe` file:

1.  Ensure you have installed the requirements (including `pyinstaller`).
2.  Run the build command:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "assets;assets" --name "ChirPet" main.py
    ```
3.  The executable will be located in the `dist/` folder.

## Controls

*   **Right-Click**: Open the context menu to Feed, Change Style, or Quit.
*   **Drag**: Click and hold to pick up the pet.
*   **Click**: Interact with the pet (wake it up, cheer it up).