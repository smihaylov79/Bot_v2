# tests/run.py

import importlib
import sys

TEST_MODULES = [
    # "tests.test_mt5_feed",
    # "tests.test_config_loader",
    # "tests.test_candles",
    "tests.test_zones",
    "tests.test_patterns",
    "tests.test_confluence",
    "tests.test_volatility",
    # "tests.test_trend",

]


def run_tests():
    print("Running tests...\n")

    for module_name in TEST_MODULES:
        print(f"--- {module_name} ---")
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "run"):
                module.run()
            else:
                print("No run() function found.")
        except Exception as e:
            print(f"❌ ERROR in {module_name}: {e}")
        print()

    print("All tests finished.")

if __name__ == "__main__":
    run_tests()
