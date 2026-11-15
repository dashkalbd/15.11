import threading
import time
from queue import Queue


# 1. Order structure
class Order:
    def __init__(self, id, customer, products, total_price):
        self.id = id
        self.customer = customer
        self.products = products
        self.total_price = total_price
        self.status = "new"

    def __str__(self):
        products_text = ", ".join(self.products)
        return f"#{self.id} | {self.customer} | {products_text} | {self.total_price} UAH | {self.status}"


# 2. Order processing system
class OrderProcessor:
    def __init__(self, workers_count=3):
        self.orders = []
        self.next_id = 1
        self.workers_count = workers_count
        self.processed_count = 0
        self.lock = threading.Lock()

    # add a new order (with checks)
    def add_order(self, customer, products, total_price):
        if customer == "":
            print("Customer name can't be empty")
            return
        if products == []:
            print("Order must have at least one product")
            return
        if total_price < 0:
            print("Total price can't be negative")
            return

        order = Order(self.next_id, customer, products, total_price)
        self.orders.append(order)
        self.next_id = self.next_id + 1
        print(f"Order #{order.id} added")

    # show all orders
    def show_orders(self):
        if self.orders == []:
            print("No orders yet")
        else:
            for order in self.orders:
                print(order)

    # one worker thread: takes orders from the queue and processes them
    def worker(self, worker_id, order_queue):
        while True:
            order = order_queue.get()

            if order is None:
                order_queue.task_done()
                break

            order.status = "processing"
            print(f"Worker {worker_id} started order #{order.id}")

            time.sleep(1)

            order.status = "done"
            with self.lock:
                self.processed_count = self.processed_count + 1

            print(f"Worker {worker_id} finished order #{order.id}")
            order_queue.task_done()

    # start processing all new orders
    def start_processing(self):
        new_orders = []
        for order in self.orders:
            if order.status == "new":
                new_orders.append(order)

        if new_orders == []:
            print("No new orders to process")
            return

        order_queue = Queue()

        threads = []
        for worker_id in range(1, self.workers_count + 1):
            thread = threading.Thread(target=self.worker, args=(worker_id, order_queue))
            threads.append(thread)
            thread.start()

        for order in new_orders:
            order_queue.put(order)

        order_queue.join()

        for thread in threads:
            order_queue.put(None)

        for thread in threads:
            thread.join()

        print("Processing finished")

    # statistics
    def show_stats(self):
        total = len(self.orders)

        not_processed = 0
        for order in self.orders:
            if order.status != "done":
                not_processed = not_processed + 1

        print(f"Total orders: {total}")
        print(f"Processed: {self.processed_count}")
        print(f"Not processed: {not_processed}")


# input helpers
def ask_price():
    while True:
        text = input("Total price: ")
        try:
            return float(text)
        except ValueError:
            print("Please enter a number")


def ask_products():
    text = input("Products (separated by commas): ")
    products = []
    for item in text.split(","):
        name = item.strip()
        if name != "":
            products.append(name)
    return products


# 5. Console menu
def menu():
    processor = OrderProcessor()

    while True:
        print()
        print("===== ORDER PROCESSOR =====")
        print("1. Add order")
        print("2. Show all orders")
        print("3. Start processing")
        print("4. Show statistics")
        print("0. Exit")
        choice = input("Your choice: ")

        if choice == "1":
            customer = input("Customer name: ").strip()
            products = ask_products()
            total_price = ask_price()
            processor.add_order(customer, products, total_price)

        elif choice == "2":
            processor.show_orders()

        elif choice == "3":
            processor.start_processing()

        elif choice == "4":
            processor.show_stats()

        elif choice == "0":
            print("\nFinal statistics:")
            processor.show_stats()
            print("Goodbye")
            break

        else:
            print("Wrong choice, try again")


menu()