# SERVER 3 — API Server (Arfian)
# Mata Kuliah: Sistem Terdistribusi (IF2228)
# Port: 6003
#
# Peran:
#   Expose REST API publik untuk client (web).
#   Data diambil dari Server 4 (Data Server) via HTTP internal.
#
# Endpoint yang tersedia:
#   GET /products          → ambil semua produk
#   GET /products/<id>     → ambil produk by ID
#
# Cara kerja:
#   Client → GET /products → Server 3 → GET /internal/products → Server 4

from flask import Flask, jsonify
import requests

# ============================================================
# KONFIGURASI — ubah IP sesuai laptop Server 4 (Riel)!
# ============================================================
API_HOST = "0.0.0.0"   # bind ke semua interface agar bisa diakses LAN
API_PORT = 6003

# IP dan port Server 4 (Data Server)
SERVER4_HOST = "10.5.6.214"  # IP laptop Riel (Server 4)
SERVER4_PORT = 6004
SERVER4_URL  = f"http://{SERVER4_HOST}:{SERVER4_PORT}"
# ============================================================

app = Flask(__name__)


# ============================================================
# HELPER — komunikasi ke Server 4
# ============================================================

def fetch_from_server4(path: str):
    """
    Kirim GET request ke Server 4 dan kembalikan (data, status_code).
    Mengembalikan (None, 503) jika Server 4 tidak dapat dihubungi.
    """
    url = f"{SERVER4_URL}{path}"
    try:
        response = requests.get(url, timeout=5)
        return response.json(), response.status_code
    except requests.exceptions.ConnectionError:
        print(f"[!] Gagal terhubung ke Server 4 di {SERVER4_URL}")
        return {"error": "Gagal terhubung ke Server 4. Pastikan server aktif."}, 503
    except requests.exceptions.Timeout:
        print("[!] Request ke Server 4 timeout")
        return {"error": "Request ke Server 4 timeout."}, 504
    except Exception as e:
        print(f"[!] Error tidak terduga: {e}")
        return {"error": f"Error tidak terduga: {str(e)}"}, 500


# ============================================================
# ENDPOINT 1 — GET /products
# Diakses oleh: Client (Web) untuk menampilkan daftar produk
# ============================================================

@app.route("/products", methods=["GET"])
def get_all_products():
    """
    Ambil semua produk dari Server 4 dan teruskan ke client.

    Alur:
        Client → GET /products → Server 3 → GET /internal/products → Server 4

    Response:
        200: { "products": [ { id, name, price, stock, image }, ... ] }
        503: { "error": "..." }  jika Server 4 tidak bisa dihubungi
    """
    data, status_code = fetch_from_server4("/internal/products")

    if status_code != 200:
        # Teruskan error dari Server 4 ke client
        return jsonify(data), status_code

    print(f"[>] GET /products — {len(data.get('products', []))} produk dikembalikan")
    return jsonify(data), 200


# ============================================================
# ENDPOINT 2 — GET /products/<id>
# Diakses oleh: Client (Web) untuk menampilkan detail satu produk
# ============================================================

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    """
    Ambil satu produk berdasarkan ID dari Server 4.

    Alur:
        Client → GET /products/<id> → Server 3 → GET /internal/products/<id> → Server 4

    Response:
        200: { id, name, price, stock, image }
        404: { "error": "Produk tidak ditemukan" }
        503: { "error": "..." }  jika Server 4 tidak bisa dihubungi
    """
    data, status_code = fetch_from_server4(f"/internal/products/{product_id}")

    if status_code == 404:
        return jsonify({"error": f"Produk dengan ID {product_id} tidak ditemukan"}), 404

    if status_code != 200:
        return jsonify(data), status_code

    print(f"[>] GET /products/{product_id} — produk: {data.get('name', '?')}")
    return jsonify(data), 200


# ============================================================
# ENDPOINT 3 — GET /health
# Cek apakah Server 3 dan koneksi ke Server 4 sehat
# (dipakai oleh halaman /status di Client)
# ============================================================

@app.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint health check untuk memverifikasi status Server 3
    dan konektivitasnya ke Server 4.
    """
    _, status_code = fetch_from_server4("/internal/products")
    server4_ok = (status_code == 200)

    return jsonify({
        "server3": "up",
        "server4_reachable": server4_ok,
        "server4_url": SERVER4_URL
    }), 200


# ============================================================
# MAIN — jalankan server di 0.0.0.0 agar bisa diakses LAN
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  SERVER 3 — API Server (Arfian)")
    print(f"  Berjalan di http://0.0.0.0:{API_PORT}")
    print(f"  Terhubung ke Server 4 di {SERVER4_URL}")
    print("  Endpoint tersedia:")
    print(f"    GET http://0.0.0.0:{API_PORT}/products")
    print(f"    GET http://0.0.0.0:{API_PORT}/products/<id>")
    print(f"    GET http://0.0.0.0:{API_PORT}/health")
    print("=" * 50)

    app.run(host=API_HOST, port=API_PORT, debug=True, threaded=True)
