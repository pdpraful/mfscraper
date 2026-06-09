#!/bin/bash
# Global CLI wrapper for International MF Capacity Scraper

# Navigate to the project directory
cd "/Volumes/PD External/Alpha-PDD/MFScraper" || exit 1

# Activate the virtual environment
source venv/bin/activate

# Pass any command line arguments directly to main.py
python3 main.py "$@"
