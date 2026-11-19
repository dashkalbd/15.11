import socket
import json

HOST = "127.0.0.1"
PORT = 5000
STATUSES = ["new", "in delivery", "delivered", "cancelled"]


def connect():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print("Connected to server")
        return sock
    except ConnectionRefusedError:
        print("Server is not available. Start server.py first.")
        return None


def send_request(sock, reader, request):
    try:
        message = json.dumps(request, ensure_ascii=False) + "\n"
        sock.sendall(message.encode("utf-8"))
        line = reader.readline()
        if line == "":
            print("Connection to server lost")
            return None
        return json.loads(line)
    except (ConnectionResetError, BrokenPipeError):
        print("Connection to server lost")
        return None


def ask_number(text):
    while True:
        answer = input(text)
        if answer.isdigit():
            return int(answer)
        print("Please enter a number")


def ask_products():
    text = input("Products (separated by commas): ")
    products = []
    for item in text.split(","):
        name = item.strip()
        if name != "":
            products.append(name)
    return products


def print_order(order):
    products_text = ", ".join(order["products"])
    print(f"#{order['id']} | {order['name']} | {order['phone']} | "
          f"{order['address']} | {products_text} | {order['status']}")


def menu():
    sock = connect()
    if sock is None:
        return
    reader = sock.makefile("r", encoding="utf-8")

    while True:
        print()
        print("===== DELIVERY CLIENT =====")
        print("1. Create order")
        print("2. My orders")
        print("3. Check order status")
        print("4. Update status (courier)")
        print("0. Exit")
        choice = input("Your choice: ")

        if choice == "1":
            request = {
                "action": "create",
                "name": input("Name: "),
                "phone": input("Phone: "),
                "address": input("Delivery address: "),
                "products": ask_products()
            }

        elif choice == "2":
            request = {"action": "my_orders", "phone": input("Your phone: ")}

        elif choice == "3":
            request = {"action": "status", "order_id": ask_number("Order number: ")}

        elif choice == "4":
            order_id = ask_number("Order number: ")
            print("Statuses:", ", ".join(STATUSES))
            request = {"action": "update_status", "order_id": order_id,
                       "status": input("New status: ").strip()}

        elif choice == "0":
            print("Goodbye")
            break

        else:
            print("Wrong choice, try again")
            continue

        response = send_request(sock, reader, request)
        if response is None:
            break

        if response["ok"] == False:
            print("Error:", response["error"])
        elif choice == "1":
            print(f"Order created, number: {response['order_id']}")
        elif choice == "2":
            if response["orders"] == []:
                print("No orders for this phone")
            else:
                for order in response["orders"]:
                    print_order(order)
        else:
            print(f"Order #{response['order_id']} status: {response['status']}")

    sock.close()


menu()