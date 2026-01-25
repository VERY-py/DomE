import socket
import struct
import threading
import select

HOST = 'localhost'
PORT = 12345
clients = []  # Список подключенных клиентов
running = True  # Флаг для остановки сервера

def handle_client(conn, addr):
    print(f"Клиент {addr} подключился")
    clients.append(conn)

    try:
        while True:
            # Получаем размер файла (4 байта)
            size_data = conn.recv(4)
            if not size_data:
                break
            file_size = struct.unpack('>L', size_data)[0]

            # Получаем JSON данные
            received_data = b''
            while len(received_data) < file_size:
                chunk = conn.recv(file_size - len(received_data))
                if not chunk:
                    break
                received_data += chunk

            if len(received_data) == file_size:
                for client in clients[:]:  # Копируем список для безопасного удаления
                    if client != conn:
                        try:
                            client.sendall(struct.pack('>L', file_size))
                            client.sendall(received_data)
                        except:
                            print(f"Ошибка отправки клиенту {client.getpeername()}")
                            clients.remove(client)

    except Exception as e:
        print(f"Ошибка клиента {addr}: {e}")
    finally:
        if conn in clients:
            clients.remove(conn)
        conn.close()
        print(f"Клиент {addr} отключился")

def console_input_handler():
    """Обработчик ввода из консоли в отдельном потоке"""
    global running
    while running:
        try:
            # Ждем ввод от пользователя
            cmd = input().strip()
            cmd = cmd.split()
            if cmd[0].lower() in ['exit', 'quit', 'stop']:
                print("Остановка сервера...")
                running = False
                break
            elif cmd[0].lower() == 'clients':
                print(f"Подключенных клиентов: {len(clients)}")
                for i, client in enumerate(clients):
                    try:
                        addr = client.getpeername()
                        print(f"  {i+1}: {addr}")
                    except:
                        print(f"  {i+1}: отключен")
                else:
                    print("Неправильное число аргументов")
            else:
                print(f"Неизвестная команда: {cmd}")
        except (EOFError, KeyboardInterrupt):
            running = False
            break

# Запуск потока для консольного ввода
console_thread = threading.Thread(target=console_input_handler, daemon=True)
console_thread.start()

# Запуск сервера
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((HOST, PORT))
server_sock.listen(5)
print(f"Сервер запущен на {HOST}:{PORT}")

try:
    while running:
        try:
            # Проверяем готовность к принятию соединения с таймаутом 0.1 сек
            ready, _, _ = select.select([server_sock], [], [], 0.1)
            if ready:
                conn, addr = server_sock.accept()
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            running = False
            break
finally:
    running = False
    print("Закрытие сервера...")
    server_sock.close()
    # Закрываем все клиентские соединения
    for client in clients[:]:
        try:
            client.close()
        except:
            pass
