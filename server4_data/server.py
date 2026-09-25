# SERVER 4 — Data Server (Riel)
# Mata Kuliah: Sistem Terdistribusi (IF2228)
# Port: 6004
# Jalankan server ini PERTAMA sebelum server lainnya!

from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

# THREADING LOCK — mencegah race condition saat transaksi
# bersamaan (misal: 2 user beli produk yang sama sekaligus)
lock = threading.Lock()

# DATA AWAL (seed) — disimpan di memori (Python dict)
# Data akan hilang jika server di-restart
# Gambar menggunakan URL dari Unsplash (butuh internet)
products = {
    1: {
        "id": 1,
        "name": "Laptop Gaming ASUS",
        "price": 12000000,
        "stock": 10,
        "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&q=80"
    },
    2: {
        "id": 2,
        "name": "Mouse Wireless Logitech",
        "price": 250000,
        "stock": 3,
        "image": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&q=80"
    },
    3: {
        "id": 3,
        "name": "Headset JBL",
        "price": 450000,
        "stock": 21,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80"
    },
    4: {
        "id": 4,
        "name": "Parfum",
        "price": 15000,
        "stock": 15,
        "image": "https://images.unsplash.com/photo-1541643600914-78b084683702?w=400&q=80"
    },
    5: {
        "id": 5,
        "name": "Fan Cooler",
        "price": 50000,
        "stock": 5,
        "image": "https://images.unsplash.com/photo-1587302164675-820fe61bbd55?w=400&q=80"
    },
    6: {
        "id": 6,
        "name": "Standholder",
        "price": 7000,
        "stock": 100,
        "image": "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400&q=80"
    },
}


# INTERNAL ENDPOINT — hanya diakses oleh Server 1, 2, dan 3
# Tidak diakses langsung oleh client/browser

# GET /internal/products
# Dipakai oleh: Server 3 (Arfian) untuk ambil semua produk
@app.route("/internal/products", methods=["GET"])
def get_all_products():
    with lock:
        data = list(products.values())
    return jsonify({"products": data}), 200


# GET /internal/products/<id>
# Dipakai oleh: Server 3 (Arfian) untuk ambil produk by ID
@app.route("/internal/products/<int:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    with lock:
        product = products.get(product_id)

    if product is None:
        return jsonify({"error": "Produk tidak ditemukan"}), 404

    return jsonify(product), 200


# GET /internal/stock/<id>
# Dipakai oleh: Server 1 (Raffi) untuk cek stok sebelum beli
#               Server 2 (Okan) untuk method get_stock()
# Response: { product_id, name, stock }
@app.route("/internal/stock/<int:product_id>", methods=["GET"])
def get_stock(product_id):
    with lock:
        product = products.get(product_id)

    if product is None:
        return jsonify({"error": "Produk tidak ditemukan"}), 404

    return jsonify({
        "product_id": product_id,
        "name": product["name"],
        "stock": product["stock"]
    }), 200


# PUT /internal/stock/<id>
# Dipakai oleh: Server 1 (Raffi) untuk kurangi stok setelah beli
#               Server 2 (Okan) untuk method update_stock()
#
# Body JSON yang dikirim server lain:
#   { "stock": <nilai stok baru> }
#
# Kenapa pakai lock di sini?
# Karena Server 1 (RPC) bisa terima banyak request bersamaan.
# Tanpa lock, dua transaksi bisa baca stok yang sama lalu
# sama-sama kurangi — hasilnya stok jadi tidak akurat.
@app.route("/internal/stock/<int:product_id>", methods=["PUT"])
def update_stock(product_id):
    data = request.get_json()

    # Validasi body request
    if data is None or "stock" not in data:
        return jsonify({"error": "Body JSON tidak valid, butuh field 'stock'"}), 400

    new_stock = data["stock"]

    # Validasi nilai stok
    if not isinstance(new_stock, int) or new_stock < 0:
        return jsonify({"error": "Nilai stok tidak valid, harus angka >= 0"}), 400

    with lock:
        product = products.get(product_id)
        if product is None:
            return jsonify({"error": "Produk tidak ditemukan"}), 404

        # Update stok di memori (atomic karena di dalam lock)
        products[product_id]["stock"] = new_stock
        updated_name = products[product_id]["name"]

    return jsonify({
        "success": True,
        "message": f"Stok '{updated_name}' berhasil diupdate menjadi {new_stock}"
    }), 200


# MAIN — jalankan server di 0.0.0.0 agar bisa diakses
# dari laptop lain dalam jaringan LAN
if __name__ == "__main__":
    print("=" * 50)
    print("  SERVER 4 — Data Server (Riel)")
    print("  Berjalan di http://0.0.0.0:6004")
    print("  Jalankan server ini PERTAMA!")
    print("=" * 50)
    # threaded=True agar Flask bisa handle request bersamaan
    app.run(host="0.0.0.0", port=6004, debug=True, threaded=True)
