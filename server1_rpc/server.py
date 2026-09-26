"""RPC server for product purchases (Server 1)."""

import pickle
import socket
import threading

import requests


# Change SERVER4_HOST to the LAN address of the Data Server.
RPC_HOST = "0.0.0.0"
RPC_PORT = 6001
SERVER4_HOST = "192.168.1.14"
SERVER4_PORT = 6004
SERVER4_URL = f"http://{SERVER4_HOST}:{SERVER4_PORT}"
SERVER4_TIMEOUT = 5

# Keep purchases handled by this process from racing each other.
purchase_lock = threading.Lock()


def response(success: bool, message: str) -> dict:
	return {"success": success, "message": message}


def buy(product_id: int, qty: int) -> dict:
	"""Check stock at Server 4 and deduct it when enough stock is available."""
	if isinstance(product_id, bool) or not isinstance(product_id, int) or product_id <= 0:
		return response(False, "ID produk tidak valid")
	if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
		return response(False, "Jumlah pembelian harus berupa bilangan bulat positif")

	stock_url = f"{SERVER4_URL}/internal/stock/{product_id}"

	# Serialize purchases handled by this RPC server to avoid local read/update races.
	with purchase_lock:
		try:
			stock_response = requests.get(stock_url, timeout=SERVER4_TIMEOUT)
			if stock_response.status_code == 404:
				return response(False, f"Produk ID {product_id} tidak ditemukan")
			stock_response.raise_for_status()

			stock_data = stock_response.json()
			current_stock = stock_data["stock"]
			product_name = stock_data["name"]

			if qty > current_stock:
				return response(
					False,
					f"Stok {product_name} tidak mencukupi. Stok tersedia: {current_stock}",
				)

			new_stock = current_stock - qty
			update_response = requests.put(
				stock_url,
				json={"stock": new_stock},
				timeout=SERVER4_TIMEOUT,
			)
			if update_response.status_code == 404:
				return response(False, f"Produk ID {product_id} tidak ditemukan")
			update_response.raise_for_status()

			return response(
				True,
				f"Pembelian {qty} {product_name} berhasil. Sisa stok: {new_stock}",
			)
		except requests.exceptions.Timeout:
			return response(False, "Request ke Server 4 timeout")
		except requests.exceptions.ConnectionError:
			return response(False, "Gagal terhubung ke Server 4. Pastikan server aktif.")
		except (requests.exceptions.RequestException, KeyError, ValueError) as error:
			print(f"[!] Kesalahan saat mengakses Server 4: {error}")
			return response(False, "Server 4 mengembalikan respons yang tidak valid")


def handle_client(connection: socket.socket, address: tuple) -> None:
	"""Unpickle one RPC request, dispatch it, and return a pickled response."""
	print(f"[+] Koneksi dari {address}")

	try:
		# The client signals the end of its request with shutdown(SHUT_WR).
		chunks = []
		while True:
			chunk = connection.recv(4096)
			if not chunk:
				break
			chunks.append(chunk)

		if not chunks:
			result = response(False, "Request kosong")
		else:
			payload = pickle.loads(b"".join(chunks))
			if not isinstance(payload, dict):
				result = response(False, "Format request tidak valid")
			elif payload.get("method") != "buy":
				result = response(False, "Method RPC tidak dikenal")
			else:
				params = payload.get("params", {})
				if not isinstance(params, dict):
					result = response(False, "Format parameter tidak valid")
				else:
					result = buy(**params)

		print(f"[<] Response untuk {address}: {result}")
		connection.sendall(pickle.dumps(result))
	except (pickle.UnpicklingError, EOFError, TypeError):
		connection.sendall(pickle.dumps(response(False, "Payload RPC tidak valid")))
	except Exception as error:
		print(f"[!] Kesalahan saat memproses {address}: {error}")
		try:
			connection.sendall(pickle.dumps(response(False, "Terjadi kesalahan pada RPC server")))
		except OSError:
			pass
	finally:
		connection.close()


def main() -> None:
	"""Start the threaded socket server so multiple clients can connect."""
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind((RPC_HOST, RPC_PORT))
		server_socket.listen()

		print("=" * 52)
		print("  SERVER 1 - RPC Server (Raffi)")
		print(f"  Listening on {RPC_HOST}:{RPC_PORT}")
		print(f"  Data Server: {SERVER4_URL}")
		print("=" * 52)

		while True:
			connection, address = server_socket.accept()
			threading.Thread(
				target=handle_client,
				args=(connection, address),
				daemon=True,
			).start()


if __name__ == "__main__":
	main()
