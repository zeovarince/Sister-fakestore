# Implementasi Toko Online dengan Sistem Terdistribusi
> Implementasi sederhana sistem terdistribusi berbasis studi kasus Toko Online menggunakan RPC, RMI, dan REST API.

**Mata Kuliah:** Sistem Terdistribusi (IF2228) — Universitas Trunojoyo Madura  
**Semester:** Gasal 2026/2027

---

## Daftar Isi
- [Deskripsi](#deskripsi)
- [Arsitektur](#arsitektur)
- [Teknologi](#teknologi)
- [Struktur Project](#struktur-project)
- [Cara Menjalankan](#cara-menjalankan)
- [Fitur](#fitur)
- [Anggota Kelompok](#anggota-kelompok)

---

## Deskripsi

Project ini mengimplementasikan sistem terdistribusi sederhana dengan studi kasus Toko Online. Sistem terdiri dari 4 server dan 1 client yang berjalan di laptop berbeda dalam satu jaringan lokal (LAN). Komunikasi antar node menggunakan tiga pendekatan: RPC (Remote Procedure Call), RMI (Remote Method Invocation), dan REST API.

---

## Arsitektur

```
┌─────────────────────────────────────────────┐
│              LAN (192.168.x.x)              │
│                                             │
│          ┌──────────────┐                   │
│          │    CLIENT    │ :5000             │
│          │   (Web App)  │                   │
│          └──────┬───────┘                   │
│                 │                           │
│     ┌───────────┼───────────┐               │
│     │           │           │               │
│     ▼           ▼           ▼               │
│  Server 1    Server 2    Server 3           │
│  (RPC):6001  (RMI):6002  (API):6003        │
│     │           │           │               │
│     └───────────┴───────────┘               │
│                 │                           │
│                 ▼                           │
│          ┌─────────────┐                    │
│          │  Server 4   │ :6004              │
│          │ (Data Server│                    │
│          └─────────────┘                    │
└─────────────────────────────────────────────┘
```

| Node | Peran | Port | Protocol |
|------|-------|------|----------|
| Client | Tampilan web user | 5000 | - |
| Server 1 | RPC Server — transaksi pembelian | 6001 | Socket + Pickle |
| Server 2 | RMI Server — cek & update stok | 6002 | Socket + Pickle |
| Server 3 | API Server — daftar produk | 6003 | HTTP/REST |
| Server 4 | Data Server — penyimpanan data | 6004 | HTTP/REST |

---

## Teknologi

- **Python 3**
- **Flask** — web client dan REST API server
- **socket + pickle** — implementasi RPC dan RMI
- **HTML** — tampilan web client
- **LAN** — jaringan lokal antar laptop

---

## Struktur Project

```
project-sisterdis/
├── client/
│   ├── app.py
│   └── templates/
│       └── index.html
├── server1_rpc/
│   └── server.py
├── server2_rmi/
│   └── server.py
├── server3_api/
│   └── server.py
├── server4_data/
│   └── server.py
├── PRD.md
├── ARCHITECTURE.md
└── README.md
```

---

## Cara Menjalankan

### Prasyarat
Pastikan semua laptop terhubung ke **jaringan WiFi/hotspot yang sama**.

Install dependency di setiap laptop:
```bash
pip install flask requests
```

---

### Langkah 1 — Jalankan Server 4 (Data Server) terlebih dahulu
> Laptop anggota yang memegang Server 4

```bash
cd server4_data
python server.py
```
Server berjalan di `http://0.0.0.0:6004`

---

### Langkah 2 — Jalankan Server 3 (API Server)
> Laptop anggota yang memegang Server 3

Sebelum menjalankan, buka `server3_api/server.py` dan sesuaikan IP Server 4:
```python
DATA_SERVER = "http://192.168.x.x:6004"  # ganti dengan IP laptop Server 4
```

```bash
cd server3_api
python server.py
```
Server berjalan di `http://0.0.0.0:6003`

---

### Langkah 3 — Jalankan Server 1 (RPC Server)
> Laptop anggota yang memegang Server 1

Sebelum menjalankan, buka `server1_rpc/server.py` dan sesuaikan IP Server 4:
```python
DATA_SERVER = "http://192.168.x.x:6004"  # ganti dengan IP laptop Server 4
```

```bash
cd server1_rpc
python server.py
```
Server berjalan di port `6001`

---

### Langkah 4 — Jalankan Server 2 (RMI Server)
> Laptop anggota yang memegang Server 2

Sebelum menjalankan, buka `server2_rmi/server.py` dan sesuaikan IP Server 4:
```python
DATA_SERVER = "http://192.168.x.x:6004"  # ganti dengan IP laptop Server 4
```

```bash
cd server2_rmi
python server.py
```
Server berjalan di port `6002`

---

### Langkah 5 — Jalankan Client
> Laptop anggota yang memegang Client

Sebelum menjalankan, buka `client/app.py` dan sesuaikan semua IP server:
```python
RPC_SERVER_HOST = "192.168.x.x"   # IP laptop Server 1
RPC_SERVER_PORT = 6001

RMI_SERVER_HOST = "192.168.x.x"   # IP laptop Server 2
RMI_SERVER_PORT = 6002

API_SERVER = "http://192.168.x.x:6003"  # IP laptop Server 3
```

```bash
cd client
python app.py
```

Buka browser dan akses `http://localhost:5000`

---

### Cara Cek IP Laptop

**Windows:**
```bash
ipconfig
# lihat bagian IPv4 Address
```

**Linux/Mac:**
```bash
ip addr
# atau
ifconfig
```

---

## Fitur

| Fitur | Method | Node yang Handle |
|-------|--------|-----------------|
| Lihat daftar produk | REST API | Client → Server 3 → Server 4 |
| Beli produk | RPC | Client → Server 1 → Server 4 |
| Cek stok produk | RMI | Client → Server 2 → Server 4 |
| Update stok produk | RMI | Client → Server 2 → Server 4 |

---

## Catatan

- Data disimpan di memori (tidak persisten jika server di-restart)
- Tidak ada autentikasi/login
- RMI diimplementasi secara manual menggunakan socket dan pickle karena Python tidak memiliki built-in RMI seperti Java
- Urutan menjalankan server penting — **Server 4 harus jalan duluan** sebelum server lainnya

---

## Anggota Kelompok

| Nama | Node |
|------|------|
| TBD | Client |
| TBD | Server 1 (RPC) |
| TBD | Server 2 (RMI) |
| TBD | Server 3 (API) |
| TBD | Server 4 (Data) |
