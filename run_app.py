"""
Flask app başlatıcısı - working directory'yi ayarla.
"""

import os
import sys

# Doğru working directory'ye geç
app_dir = r"c:\Users\iclal\OneDrive\Desktop\dualingo_clone"
os.chdir(app_dir)
sys.path.insert(0, app_dir)

# App'ı başlat
from app import app

if __name__ == "__main__":
    print("[Flask] App baslatiliyor...")
    app.run(debug=True, use_reloader=False)
