import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 5000
FILE_NAME = "orders.json"
STATUSES = ["new", "in delivery", "delivered", "cancelled"]

orders = []
next_id = 1
lock = threading.Lock()


def load_orders():
    global orders, next_id
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            orders = json.load(file)
        biggest_id = 0
        for order in orders:
            if order["id"] > biggest_id:
                biggest_id = order["id"]
        next_id = biggest_id + 1
        print(f"Loaded orders: {len(orders)}")
    except FileNotFoundError:
        print("No orders file yet, starting empty")
    except (json.JSONDecodeError, KeyError, TypeError):
        print("Orders file is broken, starting empty")
        orders = []


def save_orders():
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(orders, file, ensure_ascii=False, indent=4)


def create_order(request):
    global next_id

    name = request["name"].strip()
    phone = request["phone"].strip()
    address = request["address"].strip()
    products = request["products"]

    if name == "" or phone == "" or address == "":
        return {"ok": False, "error": "Name, phone and address can't be empty"}
    if products == []:
        return {"ok": False, "error": "Add at least one product"}

    with lock:
        order = {
            "id": next_id,
            "name": name,
            "phone": phone,
            "address": address,
            "products": products,
            "status": "new"
        }
        orders.append(order)
        next_id = next_id + 1
        save_orders()

    return {"ok": True, "order_id": order["id"]}


def get_my_orders(request):
    phone = request["phone"].strip()
    found = []
    with lock:
        for order in orders:
            if order["phone"] == phone:
                found.append(order)
    return {"ok": True, "orders": found}


def get_status(request):
    order_id = int(request["order_id"])
    with lock:
        for order in orders:
            if order["id"] == order_id:
                return {"ok": True, "order_id": order_id, "status": order["status"]}
    return {"ok": False, "error": f"Order {order_id} not found"}


def update_status(request):
    order_id = int(request["order_id"])
    new_status = request["status"]

    if new_status not in STATUSES:
        return {"ok": False, "error": "Unknown status"}

    with lock:
        for order in orders:
            if order["id"] == order_id:
                order["status"] = new_status
                save_orders()
                return {"ok": True, "order_id": order_id, "status": new_status}
    return {"ok": False, "error": f"Order {order_id} not found"}


def handle_request(request):
    action = request["action"]

    if action == "create":
        return create_order(request)
    elif action == "my_orders":
        return get_my_orders(request)
    elif action == "status":
        return get_status(request)
    elif action == "update_status":
        return update_status(request)
    else:
        return {"ok": False, "error": "Unknown action"}


def send_response(conn, response):
    message = json.dumps(response, ensure_ascii=False) + "\n"
    conn.sendall(message.encode("utf-8"))


def handle_client(conn, addr):
    print(f"Client connected: {addr}")
    reader = conn.makefile("r", encoding="utf-8")

    try:
        while True:
            line = reader.readline()
            if line == "":
                break

            try:
                request = json.loads(line)
                response = handle_request(request)
            except json.JSONDecodeError:
                response = {"ok": False, "error": "Invalid request format"}
            except (KeyError, ValueError, TypeError):
                response = {"ok": False, "error": "Wrong or missing data in request"}

            send_response(conn, response)

    except (ConnectionResetError, BrokenPipeError):
        print(f"Connection lost: {addr}")
    finally:
        conn.close()
        print(f"Client disconnected: {addr}")


def main():
    load_orders()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server started on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server.close()


main()