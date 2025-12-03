#!/usr/bin/env python3
"""
WRAPPER SCRIPT FOR ADVANCED HANDICAPPING HUB
=============================================
Entry point for GitHub Actions workflow.
Handles module imports and runs the main update.
"""

import os
import sys

# Add scripts directory to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

# Import and run main
from handicapping_hub.main import main

if __name__ == "__main__":
    sys.exit(main())
