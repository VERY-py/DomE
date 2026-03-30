import socket
import struct
import threading
import select
import logging
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GameServer:
    """Сервер для синхронизации игроков"""

    def __init__(self, host: str = 'localhost', port: int = 12345, max_clients: int = 10):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.clients: List[socket.socket] = []
        self.client_addresses: dict = {}
        self.running = True

        self._server_socket: Optional[socket.socket] = None

    def start(self) -> bool:
        """Запуск сервера"""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(self.max_clients)
            logger.info(f"Сервер запущен на {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Ошибка запуска сервера: {e}")
            return False

    def stop(self) -> None:
        """Остановка сервера"""
        self.running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass

        for client in self.clients:
            try:
                client.close()
            except Exception:
                pass

        logger.info("Сервер остановлен")

    def _handle_client(self, conn: socket.socket, addr: tuple) -> None:
        """Обработка отдельного клиента"""
        logger.info(f"Клиент {addr} подключился")
        self.clients.append(conn)
        self.client_addresses[conn] = addr

        try:
            while self.running:
                size_data = conn.recv(4)
                if not size_data:
                    break

                file_size = struct.unpack('>L', size_data)[0]

                received_data = b''
                while len(received_data) < file_size:
                    chunk = conn.recv(file_size - len(received_data))
                    if not chunk:
                        break
                    received_data += chunk

                if len(received_data) == file_size:
                    self._broadcast_data(received_data, conn)

        except (ConnectionResetError, BrokenPipeError):
            logger.warning(f"Клиент {addr} разорвал соединение")
        except Exception as e:
            logger.error(f"Ошибка клиента {addr}: {e}")
        finally:
            if conn in self.clients:
                self.clients.remove(conn)
                del self.client_addresses[conn]
            try:
                conn.close()
            except Exception:
                pass
            logger.info(f"Клиент {addr} отключился")

    def _broadcast_data(self, data: bytes, sender: socket.socket) -> None:
        """Рассылка данных всем клиентам кроме отправителя"""
        for client in self.clients[:]:
            if client != sender:
                try:
                    client.sendall(struct.pack('>L', len(data)))
                    client.sendall(data)
                except (BrokenPipeError, ConnectionResetError):
                    logger.warning(f"Клиент {self.client_addresses.get(client)} недоступен")
                    if client in self.clients:
                        self.clients.remove(client)
                except Exception as e:
                    logger.error(f"Ошибка отправки: {e}")

    def _console_handler(self) -> None:
        """Обработка команд из консоли"""
        while self.running:
            try:
                cmd = input().strip().split()
                if not cmd:
                    continue

                command = cmd[0].lower()
                if command in ['exit', 'quit', 'stop']:
                    logger.info("Остановка сервера по команде")
                    self.running = False
                    break
                elif command == 'clients':
                    logger.info(f"Подключенных клиентов: {len(self.clients)}")
                    for i, client in enumerate(self.clients):
                        addr = self.client_addresses.get(client)
                        logger.info(f"  {i + 1}: {addr}")
                elif command == 'status':
                    self._print_status()
                elif command == 'help':
                    self._print_help()
                else:
                    logger.info(f"Неизвестная команда: {command}. Введите 'help' для справки")
            except (EOFError, KeyboardInterrupt):
                logger.info("Получен сигнал остановки")
                self.running = False
                break

    def _print_status(self) -> None:
        """Вывод статуса сервера"""
        logger.info(f"=== Статус сервера ===")
        logger.info(f"Хост: {self.host}:{self.port}")
        logger.info(f"Активен: {self.running}")
        logger.info(f"Клиентов: {len(self.clients)}")
        logger.info(f"Максимум: {self.max_clients}")

    def _print_help(self) -> None:
        """Вывод справки"""
        logger.info("=== Доступные команды ===")
        logger.info("clients  - показать список подключенных клиентов")
        logger.info("status   - показать статус сервера")
        logger.info("stop     - остановить сервер")
        logger.info("exit     - остановить сервер")
        logger.info("help     - показать эту справку")

    def run(self) -> None:
        """Запуск основного цикла сервера"""
        if not self.start():
            return

        console_thread = threading.Thread(target=self._console_handler, daemon=True)
        console_thread.start()

        try:
            while self.running:
                try:
                    ready, _, _ = select.select([self._server_socket], [], [], 0.1)
                    if ready:
                        conn, addr = self._server_socket.accept()
                        client_thread = threading.Thread(
                            target=self._handle_client,
                            args=(conn, addr),
                            daemon=True
                        )
                        client_thread.start()
                except (select.error, OSError):
                    if self.running:
                        continue
                except KeyboardInterrupt:
                    logger.info("Прерывание работы")
                    break
        finally:
            self.stop()


def main() -> None:
    """Точка входа"""
    import sys

    host = 'localhost'
    port = 12345

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            logger.error(f"Неверный порт: {sys.argv[2]}")
            return

    server = GameServer(host, port)
    server.run()


if __name__ == '__main__':
    main()