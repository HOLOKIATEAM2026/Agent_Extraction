import os
import time
import uuid
import json
import requests


def _read_env_file(path: str) -> dict:
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _get_token_from_supabase(env: dict) -> str:
    supabase_url = env.get("SUPABASE_URL", "").strip().rstrip("/")
    anon_key = env.get("SUPABASE_ANON_KEY", "").strip()
    service_role_key = env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not anon_key or not service_role_key:
        raise RuntimeError("Missing SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY")

    email = f"perf+{uuid.uuid4().hex[:10]}@example.com"
    password = "PerfTest#2026!"

    admin_headers = {"apikey": service_role_key, "Authorization": f"Bearer {service_role_key}"}
    create_url = f"{supabase_url}/auth/v1/admin/users"
    payload = {"email": email, "password": password, "email_confirm": True}
    r = requests.post(create_url, headers=admin_headers, json=payload, timeout=10)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"admin create user failed: {r.status_code} {r.text[:200]}")

    token_url = f"{supabase_url}/auth/v1/token?grant_type=password"
    headers = {"apikey": anon_key, "Authorization": f"Bearer {anon_key}", "Content-Type": "application/json"}
    r2 = requests.post(token_url, headers=headers, json={"email": email, "password": password}, timeout=10)
    if r2.status_code != 200:
        raise RuntimeError(f"password grant failed: {r2.status_code} {r2.text[:200]}")
    access_token = (r2.json() or {}).get("access_token")
    if not access_token:
        raise RuntimeError("no access_token returned")
    return access_token


def main():
    env = _read_env_file(".env")
    token = _get_token_from_supabase(env)

    api_url = "http://127.0.0.1:8000/extract"
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("small.txt", open("tmp/small.txt", "rb"), "text/plain")}
    data = {"provider": "groq", "model": "llama-3.1-8b-instant", "approach": "agent", "async_mode": "false"}

    t0 = time.perf_counter()
    r = requests.post(api_url, headers=headers, files=files, data=data, timeout=600)
    dt = (time.perf_counter() - t0) * 1000.0
    print("status", r.status_code, "ms", round(dt, 1))
    print(r.text[:300])


if __name__ == "__main__":
    main()

