"""Uji otomatis yang memetakan acceptance criteria (US-1 s.d. US-6) dan NFR-01 pada LKM 9."""
from datetime import datetime, timedelta, timezone

from conftest import register


def iso(delta_hours: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=delta_hours)).isoformat()


def mk_course(client, h, name="Komputasi Awan"):
    r = client.post("/api/courses", json={"name": name}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def mk_task(client, h, course_id, title="Tugas", hours=24):
    r = client.post(
        "/api/tasks", json={"title": title, "course_id": course_id, "deadline": iso(hours)}, headers=h
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---- US-1: daftar & login -------------------------------------------------
def test_us1_login_benar_dan_salah(client, h1):
    ok = client.post("/api/auth/login", json={"email": "a@test.id", "password": "rahasia123"})
    assert ok.status_code == 200 and ok.json()["access_token"]
    bad = client.post("/api/auth/login", json={"email": "a@test.id", "password": "salah-salah"})
    assert bad.status_code == 401
    assert "access_token" not in bad.json()


def test_us1_email_duplikat_dan_password_pendek(client, h1):
    dup = client.post("/api/auth/register", json={"name": "Xx", "email": "A@test.id", "password": "rahasia123"})
    assert dup.status_code == 409
    short = client.post("/api/auth/register", json={"name": "Xx", "email": "c@test.id", "password": "123"})
    assert short.status_code == 422


def test_nfr01_tanpa_token_ditolak(client):
    for path in ("/api/tasks", "/api/courses", "/api/auth/me", "/api/admin/users"):
        assert client.get(path).status_code == 401
    assert client.get("/api/tasks", headers={"Authorization": "Bearer palsu"}).status_code == 401


def test_password_tidak_disimpan_polos(client, h1):
    from app.database import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        u = db.query(User).filter_by(email="a@test.id").one()
        assert u.password_hash != "rahasia123" and u.password_hash.startswith("$2")


# ---- US-2: tambah tugas ---------------------------------------------------
def test_us2_tambah_tugas_status_awal_todo(client, h1):
    cid = mk_course(client, h1)
    t = mk_task(client, h1, cid, "Laporan LKM 9")
    assert t["status"] == "todo"
    assert [x["id"] for x in client.get("/api/tasks", headers=h1).json()] == [t["id"]]


def test_us2_validasi_nama_atau_deadline_kosong(client, h1):
    cid = mk_course(client, h1)
    assert client.post("/api/tasks", json={"title": "  ", "course_id": cid, "deadline": iso(5)}, headers=h1).status_code == 422
    assert client.post("/api/tasks", json={"title": "A", "course_id": cid}, headers=h1).status_code == 422
    assert client.post("/api/tasks", json={"title": "A", "course_id": cid, "deadline": ""}, headers=h1).status_code == 422


# ---- US-3: filter, urutan deadline, penanda terlambat ---------------------
def test_us3_urut_deadline_filter_dan_terlambat(client, h1):
    kal, bas = mk_course(client, h1, "Kalkulus"), mk_course(client, h1, "Basis Data")
    lama = mk_task(client, h1, kal, "Lewat", hours=-5)
    dekat = mk_task(client, h1, bas, "Dekat", hours=10)
    jauh = mk_task(client, h1, kal, "Jauh", hours=200)
    data = client.get("/api/tasks", headers=h1).json()
    assert [t["title"] for t in data] == ["Lewat", "Dekat", "Jauh"]
    by = {t["title"]: t for t in data}
    assert by["Lewat"]["is_overdue"] and not by["Dekat"]["is_overdue"]
    assert by["Dekat"]["is_due_soon"] and not by["Jauh"]["is_due_soon"]
    only_kal = client.get(f"/api/tasks?course_id={kal}", headers=h1).json()
    assert {t["title"] for t in only_kal} == {"Lewat", "Jauh"}


def test_us3_tugas_selesai_tidak_dianggap_terlambat_dan_turun_ke_bawah(client, h1):
    cid = mk_course(client, h1)
    lama = mk_task(client, h1, cid, "Lewat", hours=-5)
    mk_task(client, h1, cid, "Nanti", hours=50)
    r = client.patch(f"/api/tasks/{lama['id']}/status", json={"status": "done"}, headers=h1)
    assert r.json()["is_overdue"] is False
    assert [t["title"] for t in client.get("/api/tasks", headers=h1).json()] == ["Nanti", "Lewat"]


# ---- US-4: ubah status & isolasi data --------------------------------------
def test_us4_ubah_status(client, h1):
    t = mk_task(client, h1, mk_course(client, h1))
    for s in ("doing", "done"):
        r = client.patch(f"/api/tasks/{t['id']}/status", json={"status": s}, headers=h1)
        assert r.status_code == 200 and r.json()["status"] == s
    assert client.patch(f"/api/tasks/{t['id']}/status", json={"status": "ngawur"}, headers=h1).status_code == 422


def test_us4_nfr01_tugas_pengguna_lain_ditolak(client, h1, h2):
    t = mk_task(client, h1, mk_course(client, h1))
    tid = t["id"]
    assert client.get(f"/api/tasks/{tid}", headers=h2).status_code == 404
    assert client.patch(f"/api/tasks/{tid}/status", json={"status": "done"}, headers=h2).status_code == 404
    assert client.patch(f"/api/tasks/{tid}", json={"title": "x"}, headers=h2).status_code == 404
    assert client.delete(f"/api/tasks/{tid}", headers=h2).status_code == 404
    assert client.get("/api/tasks", headers=h2).json() == []
    assert client.get(f"/api/tasks/{tid}", headers=h1).json()["status"] == "todo"


def test_nfr01_tidak_bisa_memakai_mata_kuliah_orang_lain(client, h1, h2):
    cid_a = mk_course(client, h1)
    r = client.post("/api/tasks", json={"title": "X", "course_id": cid_a, "deadline": iso(3)}, headers=h2)
    assert r.status_code == 422
    assert client.delete(f"/api/courses/{cid_a}", headers=h2).status_code == 404
    assert client.get("/api/courses", headers=h2).json() == []


# ---- US-5: ubah / hapus ----------------------------------------------------
def test_us5_ubah_deadline_dan_hapus(client, h1):
    t = mk_task(client, h1, mk_course(client, h1), hours=5)
    new_deadline = iso(100)
    r = client.patch(f"/api/tasks/{t['id']}", json={"deadline": new_deadline, "title": "Baru"}, headers=h1)
    assert r.status_code == 200 and r.json()["title"] == "Baru" and not r.json()["is_due_soon"]
    assert client.delete(f"/api/tasks/{t['id']}", headers=h1).status_code == 204
    assert client.get("/api/tasks", headers=h1).json() == []


def test_zona_waktu_disimpan_utc(client, h1):
    cid = mk_course(client, h1)
    r = client.post(
        "/api/tasks",
        json={"title": "WITA", "course_id": cid, "deadline": "2030-01-01T00:30:00+08:00"},
        headers=h1,
    )
    assert r.json()["deadline"].startswith("2029-12-31T16:30:00")


def test_mata_kuliah_hitung_dan_cascade(client, h1):
    cid = mk_course(client, h1)
    t = mk_task(client, h1, cid)
    mk_task(client, h1, cid, "B")
    client.patch(f"/api/tasks/{t['id']}/status", json={"status": "done"}, headers=h1)
    c = client.get("/api/courses", headers=h1).json()[0]
    assert (c["task_count"], c["open_task_count"]) == (2, 1)
    assert client.post("/api/courses", json={"name": "komputasi awan"}, headers=h1).status_code == 409
    assert client.delete(f"/api/courses/{cid}", headers=h1).status_code == 204
    assert client.get("/api/tasks", headers=h1).json() == []


# ---- US-6: admin -------------------------------------------------------------
def test_us6_mahasiswa_ditolak_halaman_admin(client, h1):
    assert client.get("/api/admin/users", headers=h1).status_code == 403


def test_us6_admin_nonaktifkan_akun(client, h1, admin_h):
    users = client.get("/api/admin/users", headers=admin_h).json()
    andi = next(u for u in users if u["email"] == "a@test.id")
    assert client.patch(f"/api/admin/users/{andi['id']}", json={"is_active": False}, headers=admin_h).status_code == 200
    assert client.post("/api/auth/login", json={"email": "a@test.id", "password": "rahasia123"}).status_code == 403
    # token lama pun tidak berlaku lagi
    assert client.get("/api/tasks", headers=h1).status_code == 403
    client.patch(f"/api/admin/users/{andi['id']}", json={"is_active": True}, headers=admin_h)
    assert client.get("/api/tasks", headers=h1).status_code == 200


def test_us6_admin_reset_password_dan_tidak_bisa_nonaktifkan_diri(client, h1, admin_h):
    users = client.get("/api/admin/users", headers=admin_h).json()
    andi = next(u for u in users if u["email"] == "a@test.id")
    admin = next(u for u in users if u["role"] == "admin")
    assert client.post(f"/api/admin/users/{andi['id']}/reset-password", json={"new_password": "barubaru123"}, headers=admin_h).status_code == 204
    assert client.post("/api/auth/login", json={"email": "a@test.id", "password": "barubaru123"}).status_code == 200
    assert client.patch(f"/api/admin/users/{admin['id']}", json={"is_active": False}, headers=admin_h).status_code == 400


# ---- Health ------------------------------------------------------------------
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "database": "up"}


# ---- Admin: pantau & kelola akun ----------------------------------------------
def test_admin_stats_dan_daftar_akun_tanpa_isi_tugas(client, h1, h2, admin_h):
    cid = mk_course(client, h1)
    mk_task(client, h1, cid, "RAHASIA-JUDUL-TUGAS")
    s = client.get("/api/admin/stats", headers=admin_h).json()
    assert s["total_users"] == 3 and s["total_tasks"] == 1 and s["total_courses"] == 1
    users = client.get("/api/admin/users", headers=admin_h).json()
    andi = next(u for u in users if u["email"] == "a@test.id")
    assert (andi["course_count"], andi["task_count"], andi["open_task_count"]) == (1, 1, 1)
    assert "RAHASIA-JUDUL-TUGAS" not in client.get("/api/admin/users", headers=admin_h).text
    assert client.get("/api/admin/stats", headers=h1).status_code == 403


def test_admin_last_login_tercatat(client, h1, admin_h):
    users = client.get("/api/admin/users", headers=admin_h).json()
    assert next(u for u in users if u["role"] == "admin")["last_login_at"] is not None


def test_admin_hapus_akun_beserta_datanya(client, h1, h2, admin_h):
    mk_task(client, h1, mk_course(client, h1))
    users = client.get("/api/admin/users", headers=admin_h).json()
    andi = next(u for u in users if u["email"] == "a@test.id")
    admin = next(u for u in users if u["role"] == "admin")
    assert client.delete(f"/api/admin/users/{admin['id']}", headers=admin_h).status_code == 400
    assert client.delete(f"/api/admin/users/{andi['id']}", headers=admin_h).status_code == 204
    s = client.get("/api/admin/stats", headers=admin_h).json()
    assert s["total_tasks"] == 0 and s["total_courses"] == 0 and s["total_users"] == 2
    assert client.delete(f"/api/admin/users/{andi['id']}", headers=h1).status_code in (401, 403)


# ---- Pengaturan pengingat -------------------------------------------------------
def test_pengaturan_pengingat_default_simpan_dan_validasi(client, h1, h2):
    d = client.get("/api/me/settings", headers=h1).json()
    assert d == {"reminder_enabled": True, "reminder_time": "08:00", "reminder_sound": True, "deadline_alert_hours": 3}
    new = {"reminder_enabled": True, "reminder_time": "19:30", "reminder_sound": False, "deadline_alert_hours": 24}
    assert client.put("/api/me/settings", json=new, headers=h1).json() == new
    assert client.get("/api/me/settings", headers=h1).json() == new
    assert client.get("/api/me/settings", headers=h2).json()["reminder_time"] == "08:00"  # per pengguna
    for bad in ({**new, "reminder_time": "25:00"}, {**new, "reminder_time": "7:30"}, {**new, "deadline_alert_hours": 5}):
        assert client.put("/api/me/settings", json=bad, headers=h1).status_code == 422


def test_migrasi_kolom_pada_database_lama():
    import sqlite3, os, subprocess, sys
    path = "mig_test.db"
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100), email VARCHAR(255), password_hash VARCHAR(255), role VARCHAR(20), is_active BOOLEAN, created_at DATETIME)")
    con.execute("INSERT INTO users VALUES (1,'Lama','lama@t.id','x','student',1,'2026-10-30 00:00:00')")
    con.commit(); con.close()
    code = ("import os; os.environ['DATABASE_URL']='sqlite:///./mig_test.db'\n"
            "from app.database import ensure_columns, engine\nfrom sqlalchemy import text\nensure_columns()\n"
            "r=engine.connect().execute(text('select reminder_time, reminder_enabled, deadline_alert_hours, last_login_at from users')).one()\n"
            "print(tuple(r))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=os.getcwd())
    os.remove(path)
    assert out.returncode == 0, out.stderr
    assert "('08:00', 1, 3, None)" in out.stdout
