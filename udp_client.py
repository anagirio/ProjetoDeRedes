import socket
import hashlib
import random
import time

def checksum(data):
    return hashlib.md5(data).hexdigest()

def save_file(file_name, file_data):
    new_file_name = "novo_arquivo.txt"
    with open(new_file_name, 'wb') as f:
        f.write(file_data)
    print(f"Arquivo {new_file_name} salvo com sucesso.")

def request_file(server_address, client_socket, file_name):
    try:
        request_message = f"GET /{file_name}"
        client_socket.sendto(request_message.encode('utf-8'), server_address)
        print(f"Solicitando o arquivo {file_name}...")

        while True:
            try:
                client_socket.settimeout(5.0)
                data, _ = client_socket.recvfrom(1024)
                response = data.decode('utf-8')

                if response.startswith("SIZE"):
                    file_size = int(response.split(' ')[1])
                    print(f"Tamanho do arquivo: {file_size} bytes.")
                    break
                elif response.startswith("ERROR"):
                    print(response)
                    return
            except socket.timeout:
                print("Timeout! Reenviando solicitação...")
                client_socket.sendto(request_message.encode('utf-8'), server_address)

        file_data = bytearray()
        expected_chunks = (file_size // 1024) + 1
        received_chunks = set()
        missing_chunks = set(range(expected_chunks))

        random_chunk = random.choice(list(missing_chunks))

        while missing_chunks:
            try:
                client_socket.settimeout(5.0)
                data, _ = client_socket.recvfrom(2048)

                parts = data.split(b'|', 2)
                chunk_number = int(parts[0].decode('utf-8'))
                received_checksum = parts[1].decode('utf-8')
                chunk_data = parts[2]

                if chunk_number == random_chunk:
                    discard = input(f"Descartar pedaço {random_chunk}? (s/n): ").strip().lower()
                    if discard == 's':
                        print(f"Pedaço {random_chunk} descartado.")
                        missing_chunks.add(random_chunk)
                        random_chunk = None
                        continue

                if checksum(chunk_data) == received_checksum:
                    if chunk_number not in received_chunks:
                        file_data.extend(chunk_data)
                        received_chunks.add(chunk_number)
                        missing_chunks.discard(chunk_number)
                        print(f"Pedaço {chunk_number} recebido corretamente.")

                    client_socket.sendto(f"ACK {chunk_number}".encode('utf-8'), server_address)
                else:
                    print(f"Checksum incorreto para o pedaço {chunk_number}.")
                    missing_chunks.add(chunk_number)

            except socket.timeout:
                print("Timeout ao receber pedaço. Solicitando pedaços faltantes...")
                for missing_chunk in missing_chunks:
                    client_socket.sendto(f"GET {missing_chunk}".encode('utf-8'), server_address)

        if len(file_data) == file_size:
            save_file(file_name, file_data)
        else:
            print("Erro na reconstrução do arquivo.")

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        client_socket.close()

if __name__ == "__main__":
    server_ip = input("Digite o IP do servidor: ")
    server_port = int(input("Digite a porta do servidor: "))
    file_name = input("Digite o nome do arquivo que deseja requisitar: ")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (server_ip, server_port)

    request_file(server_address, client_socket, file_name)
