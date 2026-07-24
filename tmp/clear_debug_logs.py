import requests


def main():
    r = requests.delete("http://127.0.0.1:8034/logs", timeout=10)
    print("status", r.status_code)


if __name__ == "__main__":
    main()

