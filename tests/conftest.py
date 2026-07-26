"""Add project root and ml/ to sys.path so tests can import ml.* modules."""
import sys
from pathlib import Path

# Project root (one level up from tests/)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
