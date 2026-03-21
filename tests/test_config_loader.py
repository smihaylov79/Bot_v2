# tests/test_config_loader.py

from core.config_loader import ConfigLoader

def run():
    print("Testing ConfigLoader...")

    loader = ConfigLoader()

    try:
        cfg = loader.load_all()
        print("Config loaded successfully.")
        print(cfg)
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
