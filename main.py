"""
RuneBox // Subwoofer Enclosure Lab
main.py - Application Entry Point & PyInstaller Runtime Setup
Created by NfgOdin
"""

import os
import sys

# Ensure local directory is on python path for frozen execution
if getattr(sys, 'frozen', False):
    application_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

if application_path not in sys.path:
    sys.path.insert(0, application_path)

from gui import RuneBoxApp


def main():
    """Launch the RuneBox Desktop Application."""
    app = RuneBoxApp()
    app.mainloop()


if __name__ == "__main__":
    main()
