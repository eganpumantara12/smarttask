# SmartTask — Sistem Pengelolaan Tugas Mahasiswa

Proyek Komputasi Awan, Kelompok 7 (S1 Pendidikan Komputer). Implementasi **MVP (BL-01 s.d. BL-07)** dari LKM 9,
ditambah pengelolaan akun admin (BL-08) dan skrip backup/restore (BL-09).

| Lapisan | Teknologi |
|---|---|
| Frontend | React 18 + Vite (responsif HP & laptop) |
| Backend | FastAPI (Python), JWT, bcrypt, dokumentasi OpenAPI di `/api/docs` |
| Database | PostgreSQL 16 (SQLite otomatis untuk pengembangan lokal) |
| Deploy | Docker Compose + Caddy (HTTPS otomatis), health check, restart otomatis |
| CI | GitHub Actions (uji backend, build frontend, build image) |

## Struktur

```
backend/    API FastAPI (app/routers: auth, courses, tasks, admin) + tests/
frontend/   React (src/pages, src/components)
deploy/     Caddyfile (reverse proxy HTTPS)
scripts/    backup.sh, restore.sh, loadtest.py
docker-compose.yml, .env.example
```

## 1. Jalankan di laptop (tanpa Docker)

Backend (terminal 1):
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
ADMIN_EMAIL=admin@smarttask.id ADMIN_PASSWORD=admin12345 uvicorn app.main:app --reload --port 8000
```
Frontend (terminal 2):
```bash
cd frontend
npm install
npm run dev          # buka http://localhost:5173
```
Dokumentasi API: http://localhost:8000/api/docs

## 2. Jalankan dengan Docker Compose (sama seperti di server)

```bash
cp .env.example .env     # isi POSTGRES_PASSWORD, SECRET_KEY, ADMIN_PASSWORD
docker compose up -d --build
```
Buka **https://localhost** (browser akan memberi peringatan sertifikat lokal; lanjutkan saja).
Cek status: `docker compose ps` — kolom *healthy* harus muncul untuk `db` dan `api`.

## 3. Deploy ke VPS / cloud (target demo: URL HTTPS publik)

1. Sewa VPS kecil (Ubuntu), pasang Docker + Docker Compose plugin. Buka port 80 dan 443.
2. Arahkan domain/subdomain (A record) ke IP VPS. Alternatif gratis: DuckDNS.
3. Salin proyek ke VPS (`git clone`), `cp .env.example .env`, lalu set `DOMAIN=tugas.contoh.id` dan isi password/secret.
4. `docker compose up -d --build` — Caddy mengurus sertifikat Let's Encrypt otomatis.
5. Backup harian: `crontab -e` → `0 2 * * * cd /opt/smarttask && ./scripts/backup.sh`.
   Latih restore sebelum demo: `./scripts/restore.sh backups/<file>.sql.gz`.

## Pengujian

```bash
cd backend && pytest -q                       # 23 uji: acceptance criteria US-1..US-6 + NFR-01
python3 scripts/loadtest.py http://localhost:8000   # NFR-02: 30 pengguna bersamaan, p95 <= 2 dtk
```
Hasil di lingkungan pengembangan: 23/23 uji lolos; uji beban 600 request, p95 ≈ 281 ms.

## Pemetaan ke LKM 9

| Backlog | Fitur | Lokasi |
|---|---|---|
| BL-01 | Daftar, login, logout, data per pengguna | `routers/auth.py`, `deps.py`, `pages/AuthPage.jsx` |
| BL-02 | Mata kuliah | `routers/courses.py`, `pages/CoursesPage.jsx` |
| BL-03/04/06 | Tambah, lihat, ubah, hapus, ubah status tugas | `routers/tasks.py`, `components/TaskForm.jsx`, `TaskCard.jsx` |
| BL-05 | Filter per mata kuliah, urut deadline, penanda terlambat/segera | `routers/tasks.py` (`list_tasks`), `pages/TasksPage.jsx` |
| BL-07 | Docker, HTTPS, health check | `docker-compose.yml`, `deploy/Caddyfile`, `/api/health` |
| BL-08 | Kelola akun admin | `routers/admin.py`, `pages/AdminPage.jsx` |
| BL-09 | Backup & restore | `scripts/backup.sh`, `scripts/restore.sh` |
| BL-10 | Pengingat harian + peringatan sebelum deadline, bisa diatur tiap pengguna (jam, bunyi, notifikasi browser) | `routers/me.py`, `components/ReminderEngine.jsx`, `pages/SettingsPage.jsx` |

| NFR | Penerapan |
|---|---|
| NFR-01 Keamanan | Semua endpoint (selain login/daftar) wajib JWT; password di-hash bcrypt; semua query tugas/mata kuliah difilter `user_id` (milik orang lain → 404); HTTPS lewat Caddy; secret via environment variable |
| NFR-02 Kinerja | Indeks `(user_id, deadline)`; `scripts/loadtest.py` |
| NFR-03 Ketersediaan | `restart: unless-stopped`, health check, backup/restore |
| NFR-04 Biaya | Satu VPS kecil, tanpa layanan berbayar tambahan |
| NFR-05 Maintainability | Modul terpisah, konfigurasi via env, log JSON terstruktur, OpenAPI otomatis |
| NFR-06 Skalabilitas | API stateless (token JWT), dapat dijalankan >1 instance |

## Pengingat (menu "Pengingat")
Setiap pengguna mengatur sendiri: pengingat harian (on/off + jam), peringatan 1/3/6/12/24 jam sebelum deadline, bunyi, dan notifikasi browser. Pengaturan tersimpan di server (sama di HP dan laptop). Pengingat berjalan selama SmartTask terbuka di browser; pengingat saat browser tertutup (email/web push) adalah pengembangan lanjutan.

## Akun admin
Admin memantau akun: statistik, daftar akun (login terakhir, jumlah mata kuliah/tugas), cari/filter, nonaktifkan, reset password, hapus akun. Admin **tidak** dapat melihat judul/isi tugas pengguna.

Dibuat otomatis dari `ADMIN_EMAIL` dan `ADMIN_PASSWORD` saat API pertama kali berjalan. Pendaftaran publik selalu berperan *mahasiswa*.

## Catatan keamanan sebelum demo
- Ganti `SECRET_KEY` dan semua password di `.env`; jangan commit `.env`.
- Token disimpan di `localStorage` (cukup untuk prototipe kuliah). Untuk produksi, pertimbangkan cookie `HttpOnly`.
