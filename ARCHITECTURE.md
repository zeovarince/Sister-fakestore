# Architecture & Schema
## Toko Online Terdistribusi — IF2228

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        LAN (192.168.x.x)                    │
│                                                             │
│   ┌──────────────┐                                          │
│   │    CLIENT    │  :5000                                   │
│   │   (Web App)  │                                          │
│   └──────┬───────┘                                          │
│          │                                                  │
│          ├─── RPC call (socket+pickle) ───────────────────┐ │
│          │                                                │ │
│          ├─── RMI call (socket+object) ────────────────┐  │ │
│          │                                             │  │ │
│          └─── REST API (HTTP) ──────────────────────┐  │  │ │
│                                                     │  │  │ │
│   ┌─────────────────┐   ┌─────────────────┐         │  │  │ │
│   │    SERVER 3     │   │    SERVER 1     │         │  │  │ │
│   │   (API Server)  │   │   (RPC Server)  │◄────────┘  │  │ │
│   │     :6003       │◄──┤─────────────────┤            │  │ │
│   └────────┬────────┘   │  handle beli    │◄───────────┘  │ │
│            │            └────────┬────────┘               │ │
│            │                    │                         │ │
│            │            ┌───────┘                         │ │
│            │            │                                 │ │
│            ▼            ▼                                 │ │
│   ┌─────────────────────────────┐   ┌─────────────────┐  │ │
│   │         SERVER 4            │   │    SERVER 2     │  │ │
│   │       (Data Server)         │◄──│   (RMI Server)  │◄─┘ │
│   │          :6004              │   │     :6002       │    │
│   │   simpan semua data         │   │  handle stok    │    │
│   └─────────────────────────────┘   └─────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Communication Flow

### 2.1 Lihat Daftar Produk
```
Client
  │
  │── GET /products ──► Server 3 (API Server)
                              │
                              │── GET /internal/products ──► Server 4 (Data Server)
                              │                                      │
                              │◄─────────── JSON produk ─────────────┘
                              │
  ◄─── JSON produk ───────────┘
```

### 2.2 Beli Produk (RPC)
```
Client
  │
  │── RPC call: buy(product_id, qty) ──► Server 1 (RPC Server)
                                               │
                                               │── GET /internal/stock/<id> ──► Server 4
                                               │◄────────── stok tersedia ─────────────┘
                                               │
                                               │── PUT /internal/stock/<id> ──► Server 4
                                               │◄────────── stok diupdate ─────────────┘
                                               │
  ◄── RPC response: {success, message} ────────┘
```

### 2.3 Cek & Update Stok (RMI)
```
Client
  │
  │── RMI call: StockService.get_stock(product_id) ──► Server 2 (RMI Server)
                                                              │
                                                              │── GET /internal/stock/<id> ──► Server 4
                                                              │◄──────────── data stok ──────────────┘
                                                              │
  ◄── RMI response: {product_id, stock} ────────────────────┘
```

---

## 3. Node Schema

### 3.1 Client (Web App) — Port 5000
```
client/
├── app.py              # Flask app, routing, panggil RPC/RMI/API
└── templates/
    └── index.html      # Tampilan web sederhana
```

**Responsibilities:**
- Render tampilan web
- Kirim RPC call ke Server 1
- Kirim RMI call ke Server 2
- Kirim HTTP request ke Server 3

---

### 3.2 Server 1 (RPC Server) — Port 6001
```
server1_rpc/
└── server.py           # Socket server, terima RPC call, proses transaksi
```

**RPC Methods:**
```python
buy(product_id: int, qty: int) -> dict
# return: { success: bool, message: str }
```

**Flow:**
1. Terima request via socket
2. Unmarshal payload dengan pickle
3. Cek stok ke Server 4
4. Kurangi stok di Server 4
5. Marshal response dan kirim balik ke client

---

### 3.3 Server 2 (RMI Server) — Port 6002
```
server2_rmi/
└── server.py           # Socket server, terima RMI call, invoke object method
```

**RMI Object — StockService:**
```python
class StockService:
    def get_stock(self, product_id: int) -> dict
    # return: { product_id: int, name: str, stock: int }

    def update_stock(self, product_id: int, qty: int) -> dict
    # return: { success: bool, message: str }
```

**Flow:**
1. Terima request via socket
2. Deserialize object method call
3. Invoke method pada object StockService
4. Communicate ke Server 4
5. Serialize response dan kirim balik ke client

---

### 3.4 Server 3 (API Server) — Port 6003
```
server3_api/
└── server.py           # Flask app, expose REST API produk
```

**Endpoints:**
```
GET  /products           → ambil semua produk
GET  /products/<id>      → ambil produk by ID
```

**Response Format:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Produk A",
      "price": 10000,
      "stock": 50
    }
  ]
}
```

---

### 3.5 Server 4 (Data Server) — Port 6004
```
server4_data/
└── server.py           # Flask app, internal API, simpan data di memori
```

**Internal Endpoints (tidak diakses client langsung):**
```
GET  /internal/products           → ambil semua produk
GET  /internal/products/<id>      → ambil produk by ID
GET  /internal/stock/<id>         → ambil stok produk
PUT  /internal/stock/<id>         → update stok produk
```

**Data Schema (in-memory):**
```python
products = {
    1: { "id": 1, "name": "Produk A", "price": 10000, "stock": 50 },
    2: { "id": 2, "name": "Produk B", "price": 25000, "stock": 30 },
    3: { "id": 3, "name": "Produk C", "price": 15000, "stock": 20 },
}
```

---

## 4. Protocol Schema

### 4.1 RPC Protocol (Client ↔ Server 1)
```
Request (pickle serialized):
{
    "method": "buy",
    "params": {
        "product_id": 1,
        "qty": 2
    }
}

Response (pickle serialized):
{
    "success": true,
    "message": "Pembelian berhasil"
}
```

### 4.2 RMI Protocol (Client ↔ Server 2)
```
Request (pickle serialized):
{
    "object": "StockService",
    "method": "get_stock",
    "params": {
        "product_id": 1
    }
}

Response (pickle serialized):
{
    "product_id": 1,
    "name": "Produk A",
    "stock": 50
}
```

### 4.3 REST API Protocol (Client ↔ Server 3)
```
Request:
GET /products HTTP/1.1
Host: 192.168.x.x:6003

Response:
HTTP/1.1 200 OK
Content-Type: application/json

{
    "products": [...]
}
```

---

## 5. IP & Port Summary

| Node | IP (contoh) | Port | Protocol |
|------|-------------|------|----------|
| Client | 192.168.1.10 | 5000 | - |
| Server 1 (RPC) | 192.168.1.11 | 6001 | Socket + Pickle |
| Server 2 (RMI) | 192.168.1.12 | 6002 | Socket + Pickle |
| Server 3 (API) | 192.168.1.13 | 6003 | HTTP/REST |
| Server 4 (Data) | 192.168.1.14 | 6004 | HTTP/REST |

> **Catatan:** IP di atas hanya contoh. Sesuaikan dengan IP aktual masing-masing laptop saat koneksi ke jaringan yang sama.
