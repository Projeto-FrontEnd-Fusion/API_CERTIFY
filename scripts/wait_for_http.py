"""Wait for an HTTP endpoint without hiding startup failures in CI."""
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

deadline = time.monotonic() + 60
while time.monotonic() < deadline:
    try:
        with urlopen(sys.argv[1], timeout=2) as response:
            if response.status == 200:
                raise SystemExit(0)
    except (URLError, TimeoutError):
        time.sleep(1)
raise SystemExit('API did not become ready within 60 seconds')
