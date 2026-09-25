# SERVER 2 — RMI Server (Okan)
# Cara kerja RMI di sini:
#   1. Client kirim payload pickle berisi: { object, method, params }
#   2. Server lookup object "StockService" dan panggil methodnya
#   3. Method berkomunikasi ke Server 4 (Riel) via HTTP
#   4. Hasil di-pickle lalu dikirim balik ke client

import socket
import pickle
import threading
import requests

# ============================================================
# KONFIGURASI — ubah IP sesuai laptop masing-masing!
# ============================================================
RMI_HOST = "0.0.0.0"       # bind ke semua interface agar bisa diakses LAN
RMI_PORT = 6002

# IP dan port Server 4 (Riel) — Data Server
SERVER4_HOST = "192.168.1.14"   # <-- ganti sesuai IP laptop Riel
SERVER4_PORT = 6004
SERVER4_URL  = f"http://{SERVER4_HOST}:{SERVER4_PORT}"
# ============================================================


# ============================================================
# CLASS StockService — Remote Object yang di-invoke oleh client
# ============================================================
class StockService:
    """
    Remote Object yang bisa dipanggil oleh client via RMI.
    Semua komunikasi ke Server 4 dilakukan di sini.
    """

    def get_stock(self, product_id: int) -> dict:
        """
        Ambil info stok produk berdasarkan product_id.

        Args:
            product_id (int): ID produk yang ingin dicek.

        Returns:
            dict: { product_id, name, stock } jika berhasil
                  { error }                   jika produk tidak ditemukan
        """
        url = f"{SERVER4_URL}/internal/stock/{product_id}"

        try:
            # Kirim GET request ke Server 4 untuk ambil stok
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                return {
                    "product_id": data["product_id"],
                    "name":       data["name"],
                    "stock":      data["stock"]
                }
            elif response.status_code == 404:
                return {"error": f"Produk ID {product_id} tidak ditemukan"}
            else:
                return {"error": f"Server 4 error: {response.status_code}"}

        except requests.exceptions.ConnectionError:
            return {"error": "Gagal konek ke Server 4. Pastikan Server 4 sudah jalan."}
        except requests.exceptions.Timeout:
            return {"error": "Request ke Server 4 timeout"}
        except Exception as e:
            return {"error": f"Error tidak terduga: {str(e)}"}

    def update_stock(self, product_id: int, qty: int) -> dict:
        """
        Update stok produk. Stok baru = stok sekarang + qty.
        qty bisa positif (tambah stok) atau negatif (kurangi stok).

        Args:
            product_id (int): ID produk yang ingin diupdate.
            qty        (int): Jumlah perubahan stok (+/-)

        Returns:
            dict: { success, message } jika berhasil
                  { error }            jika gagal
        """
        # Langkah 1: Ambil stok saat ini dari Server 4
        current = self.get_stock(product_id)

        if "error" in current:
            # Produk tidak ditemukan atau Server 4 down
            return {"success": False, "message": current["error"]}

        current_stock = current["stock"]
        new_stock     = current_stock + qty

        # Langkah 2: Validasi — stok tidak boleh negatif
        if new_stock < 0:
            return {
                "success": False,
                "message": f"Stok tidak mencukupi. Stok saat ini: {current_stock}"
            }

        # Langkah 3: Kirim PUT request ke Server 4 untuk update stok
        url = f"{SERVER4_URL}/internal/stock/{product_id}"

        try:
            response = requests.put(
                url,
                json={"stock": new_stock},
                timeout=5
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Stok '{current['name']}' berhasil diupdate: "
                               f"{current_stock} -> {new_stock}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Gagal update stok di Server 4: {response.status_code}"
                }

        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Gagal konek ke Server 4"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Request ke Server 4 timeout"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}


# ============================================================
# REGISTRY — daftar object yang tersedia untuk di-invoke
# ============================================================
# Tambahkan object lain di sini jika diperlukan di masa depan
OBJECT_REGISTRY = {
    "StockService": StockService()
}


# ============================================================
# HANDLER — proses satu koneksi client secara thread terpisah
# ============================================================
def handle_client(conn: socket.socket, addr):
    """
    Menerima satu koneksi, membaca payload pickle, invoke method
    pada remote object, lalu mengirim response pickle kembali.

    Payload yang diterima (dict):
        {
            "object": "StockService",       # nama class remote object
            "method": "get_stock",          # nama method yang dipanggil
            "params": { "product_id": 1 }   # keyword args method
        }

    Response yang dikirim (dict):
        Hasil return value dari method yang dipanggil.
    """
    print(f"[+] Koneksi masuk dari {addr}")

    try:
        # ---- RECEIVE: baca semua data dari client ----
        chunks = []
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)

        raw_data = b"".join(chunks)

        if not raw_data:
            print(f"[-] Data kosong dari {addr}")
            return

        # ---- UNMARSHAL: decode payload dengan pickle ----
        payload = pickle.loads(raw_data)
        print(f"[>] Request: object={payload.get('object')}, "
              f"method={payload.get('method')}, "
              f"params={payload.get('params')}")

        object_name = payload.get("object")
        method_name = payload.get("method")
        params      = payload.get("params", {})

        # ---- LOOKUP: cari object di registry ----
        remote_object = OBJECT_REGISTRY.get(object_name)

        if remote_object is None:
            result = {"error": f"Object '{object_name}' tidak ditemukan di registry"}
        else:
            # ---- INVOKE: panggil method pada object ----
            method = getattr(remote_object, method_name, None)

            if method is None:
                result = {"error": f"Method '{method_name}' tidak ada di '{object_name}'"}
            else:
                # Panggil method dengan params sebagai keyword arguments
                result = method(**params)

        print(f"[<] Response: {result}")

        # ---- MARSHAL: encode response dengan pickle dan kirim ----
        conn.sendall(pickle.dumps(result))

    except pickle.UnpicklingError:
        error_resp = {"error": "Payload tidak bisa di-unpickle"}
        conn.sendall(pickle.dumps(error_resp))
        print(f"[!] UnpicklingError dari {addr}")
    except Exception as e:
        error_resp = {"error": f"Server error: {str(e)}"}
        try:
            conn.sendall(pickle.dumps(error_resp))
        except Exception:
            pass
        print(f"[!] Exception saat handle {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Koneksi {addr} ditutup")


# ============================================================
# MAIN — jalankan socket server RMI
# ============================================================
def start_rmi_server():
    """
    Membuat socket server yang listen di RMI_HOST:RMI_PORT.
    Setiap koneksi masuk dihandle di thread terpisah supaya
    server bisa terima banyak request sekaligus.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # SO_REUSEADDR: supaya port bisa langsung dipakai lagi setelah restart
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((RMI_HOST, RMI_PORT))
    server_socket.listen(5)   # queue max 5 koneksi pending

    print("=" * 50)
    print("  SERVER 2 — RMI Server (Okan)")
    print(f"  Berjalan di {RMI_HOST}:{RMI_PORT}")
    print(f"  Terhubung ke Server 4 di {SERVER4_URL}")
    print("  Menunggu koneksi dari client...")
    print("=" * 50)

    try:
        while True:
            # Tunggu koneksi baru masuk (blocking)
            conn, addr = server_socket.accept()

            # Spawn thread baru untuk handle koneksi ini
            # agar main thread tetap bisa terima koneksi lain
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

    except KeyboardInterrupt:
        print("\n[!] Server dihentikan oleh user")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_rmi_server()