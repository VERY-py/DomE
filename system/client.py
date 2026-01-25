import socket
import struct
import threading

class Client:
    def __init__(self, host='localhost', port=12345):
        self.HOST = host
        self.PORT = port
        self.JSON_FILE = 'example.json'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def receive_files(self):
        while True:
            try:
                size_data = self.sock.recv(4)
                if not size_data:
                    break
                file_size = struct.unpack('>L', size_data)[0]

                received_data = b''
                while len(received_data) < file_size:
                    chunk = self.sock.recv(file_size - len(received_data))
                    if not chunk:
                        break
                    received_data += chunk

                if len(received_data) == file_size:
                    with open('json/input_info.json', 'wb') as f:
                        f.write(received_data)
            except:
                break

    def connect(self):
        self.sock.connect((self.HOST, self.PORT))
        receive_thread = threading.Thread(target=self.receive_files, args=())
        receive_thread.daemon = True
        receive_thread.start()

    def send_to_server(self, json_path):
        with open(json_path, 'rb') as f:
            json_data = f.read()

        file_size = len(json_data)

        try:
            self.sock.sendall(struct.pack('>L', file_size))
            self.sock.sendall(json_data)
            return False
        except ConnectionRefusedError:
            print("Сервер не активен или неправильное подключение")
            return True
        except socket.timeout:
            print("Нет доступа к интернету")
            return True
        except:
            return True