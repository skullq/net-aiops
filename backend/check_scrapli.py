try:
    import scrapli
    print("Scrapli version:", scrapli.__version__)
    from scrapli.driver.core import IOSXEDriver
    print("IOSXEDriver imported successfully!")
except Exception as e:
    import traceback
    print("Failed to import scrapli:", e)
    traceback.print_exc()

try:
    import hier_config
    print("hier_config version:", hier_config.__version__)
    from hier_config import Host, Platform
    print("hier_config imported successfully!")
except Exception as e:
    import traceback
    print("Failed to import hier_config:", e)
    traceback.print_exc()
