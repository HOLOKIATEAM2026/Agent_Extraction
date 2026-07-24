import json
import requests


def main():
    r = requests.get("http://127.0.0.1:8034/logs", params={"last": 300}, timeout=10)
    r.raise_for_status()
    data = r.json()
    print("events", len(data))
    for e in data:
        ev = e.get("event")
        ms = e.get("ms")
        if ms is None:
            continue
        try:
            ms_val = float(ms)
        except Exception:
            continue
        print(f"{ev}\t{ms_val:.1f}")


if __name__ == "__main__":
    main()

