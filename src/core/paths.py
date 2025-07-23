import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")
ASSETS_DIR = os.path.join(DIST_DIR, "assets")
WORKFLOWS_DIR = os.path.join(BASE_DIR, "workflows")

