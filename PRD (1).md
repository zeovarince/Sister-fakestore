# Product Requirements Document (PRD)
## Toko Online Terdistribusi
**Mata Kuliah:** Sistem Terdistribusi (IF2228)  
**Semester:** Gasal 2026/2027  
**Universitas:** Universitas Trunojoyo Madura

---

## 1. Deskripsi Project

Project ini merupakan implementasi sederhana sistem terdistribusi berbasis studi kasus Toko Online. Sistem dibangun menggunakan Python 3 dengan komunikasi antar node melalui RPC (Remote Procedure Call), RMI (Remote Method Invocation), dan REST API. Setiap node berjalan di laptop berbeda dalam satu jaringan lokal (LAN).

---

## 2. Tujuan

- Mengimplementasikan konsep RPC sesuai materi perkuliahan (socket + pickle)
- Mengimplementasikan konsep RMI berbasis object invocation
- Menerapkan komunikasi antar node via REST API
- Membangun sistem terdistribusi sederhana dengan 4 server dan 1 client

---

## 3. Arsitektur Sistem

```
Client (Web)
      │
      ├──→ RPC call ──→ Server 1 (RPC Server)   → transaksi pembelian
      │
      ├──→ RMI call ──→ Server 2 (RMI Server)   → cek & update stok
      │
      └──→ REST API ──→ Server 3 (API Server)   → lihat daftar produk
                               │
                        Server 4 (Data Server)  ← diakses semua server
```

### Node dan Peran

| Node | Peran | Port |
|------|-------|------|
| Client | Tampilan web untuk user | 5000 |
| Server 1 | RPC Server — handle transaksi pembelian | 6001 |
| Server 2 | RMI Server — handle cek & update stok | 6002 |
| Server 3 | API Server — expose REST API daftar produk | 6003 |
| Server 4 | Data Server — menyimpan semua data | 6004 |

### Jaringan

Semua node terhubung dalam satu jaringan lokal (WiFi/hotspot yang sama). Komunikasi menggunakan IP lokal masing-masing laptop.

---

## 4. Fitur

### 4.1 Client (Web)
- Lihat daftar produk (nama, harga, stok)
- Beli produk (kurangi stok)
- Cek stok produk
- Tambah stok produk

### 4.2 Server 1 — RPC Server
- Menerima request pembelian dari client via RPC
- Memvalidasi stok ke Server 4
- Memproses transaksi dan mengurangi stok

### 4.3 Server 2 — RMI Server
- Menerima request cek stok via RMI
- Menerima request update stok via RMI
- Berkomunikasi dengan Server 4 untuk baca/tulis data

### 4.4 Server 3 — API Server
- Expose REST API GET `/products` — ambil semua produk
- Expose REST API GET `/products/<id>` — ambil produk by ID
- Mengambil data dari Server 4

### 4.5 Server 4 — Data Server
- Menyimpan data produk (id, nama, harga, stok)
- Expose internal API untuk diakses Server 1, 2, dan 3
- Tidak diakses langsung oleh client

---

## 5. Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Bahasa | Python 3 |
| Web Client | Flask + HTML |
| RPC | Python socket + pickle |
| RMI | Python socket + object serialization |
| REST API | Flask |
| Data | Python dict / JSON file (tanpa database eksternal) |
| Jaringan | LAN (IP lokal) |

---

## 6. Struktur Folder

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
└── server4_data/
    └── server.py
```

---

## 7. Alur Komunikasi

### Beli Produk
1. User klik "Beli" di web client
2. Client kirim RPC call ke Server 1
3. Server 1 cek stok ke Server 4
4. Jika stok tersedia, Server 1 minta Server 4 kurangi stok
5. Server 1 kembalikan hasil ke client
6. Client tampilkan notifikasi berhasil/gagal

### Cek Stok
1. User klik "Cek Stok" di web client
2. Client kirim RMI call ke Server 2
3. Server 2 ambil data stok dari Server 4
4. Server 2 kembalikan hasil ke client
5. Client tampilkan info stok

### Lihat Produk
1. User buka halaman utama web client
2. Client hit REST API ke Server 3
3. Server 3 ambil data dari Server 4
4. Server 3 return JSON ke client
5. Client render daftar produk

---

## 8. Batasan

- Tidak ada autentikasi/login
- Data disimpan di memori (tidak persisten jika server restart)
- Hanya berjalan di jaringan lokal
- Implementasi RMI dilakukan manual (Python tidak punya built-in RMI seperti Java)

---

## 9. Anggota Kelompok

| Nama | Node |
|------|------|
| TBD | Client |
| TBD | Server 1 (RPC) |
| TBD | Server 2 (RMI) |
| TBD | Server 3 (API) |
| TBD | Server 4 (Data) |
