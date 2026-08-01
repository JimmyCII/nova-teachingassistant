# tests/conftest.py
# Tests must never touch the real Firestore request log — force the CSV backend
# before any module can lazily select a backend.
import os

os.environ["NOVA_MEMORY_BACKEND"] = "csv"
