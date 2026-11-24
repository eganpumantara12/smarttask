"""Uji beban sederhana untuk NFR-02: 30 pengguna bersamaan, 100 tugas per pengguna, hitung persentil ke-95.
Pemakaian: python3 scripts/loadtest.py http://localhost:8000   (hanya stdlib)"""
import json, statistics, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
USERS, TASKS = 30, 100
RUN = int(time.time())


def call(path, token=None, method="GET", body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read() or "null")
    return data, time.perf_counter() - t0


def prepare(i):
    d, _ = call("/api/auth/register", method="POST", body={"name": f"Load {i}", "email": f"load{RUN}_{i}@t.id", "password": "loadtest123"})
    tok = d["access_token"]
    c, _ = call("/api/courses", tok, "POST", {"name": "MK"})
    for n in range(TASKS):
        dl = (datetime.now(timezone.utc) + timedelta(hours=n - 20)).isoformat()
        call("/api/tasks", tok, "POST", {"title": f"T{n}", "course_id": c["id"], "deadline": dl})
    return tok


def work(tok):
    lat = []
    for _ in range(10):
        lat.append(call("/api/tasks", tok)[1])
        lat.append(call("/api/courses", tok)[1])
    return lat


with ThreadPoolExecutor(USERS) as ex:
    tokens = list(ex.map(prepare, range(USERS)))
    t0 = time.perf_counter()
    all_lat = [x for chunk in ex.map(work, tokens) for x in chunk]
dur = time.perf_counter() - t0
all_lat.sort()
p95 = all_lat[int(len(all_lat) * 0.95) - 1]
print(f"{len(all_lat)} request dari {USERS} pengguna bersamaan ({TASKS} tugas/pengguna) dalam {dur:.1f}s")
print(f"rata-rata {statistics.mean(all_lat)*1000:.0f} ms | p95 {p95*1000:.0f} ms | maks {all_lat[-1]*1000:.0f} ms")
print("NFR-02:", "LOLOS (p95 <= 2 detik)" if p95 <= 2 else "GAGAL")
