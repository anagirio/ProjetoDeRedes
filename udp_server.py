import socket
import os
import hashlib

def checksum(data):
    return hashlib.md5(data).hexdigest()

def create_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_ip = '0.0.0.0'
    server_port = 12345
    server_socket.bind((server_ip, server_port))

    print(f"Servidor UDP iniciado na porta {server_port}...")

    return server_socket



def send_file(file_name, client_address, server_socket):
    try:
        file_size = os.path.getsize(file_name)
        print(f"Enviando arquivo: {file_name}, Tamanho: {file_size} bytes.")

        server_socket.sendto(f"SIZE {file_size}".encode('utf-8'), client_address)
        buffer_size = 1024  # Tamanho do buffer em bytes
        chunks = []

        with open(file_name, 'rb') as f:
            chunk_number = 0
            while True:
                chunk_data = f.read(buffer_size)
                if not chunk_data:
                    print(f"Arquivo {file_name} enviado com sucesso. ")
                    break

                # Cria o pacote com o checksum e número do pedaço
                chunk_checksum = checksum(chunk_data)
                header = f"{chunk_number}|{chunk_checksum}".encode('utf-8')
                packet = header + b'|' + chunk_data


                while True:
                    # Send the packet
                    server_socket.sendto(packet, client_address)
                    # print(f"Enviado pedaço {chunk_number} com {len(chunk_data)} bytes.")

                    try:
                        # Wait for acknowledgment (ACK)
                        server_socket.settimeout(None)  # Timeout
                        ack, _ = server_socket.recvfrom(1024)
                        if ack.decode('utf-8') == f"ACK {chunk_number}":
                            break  # Move to the next chunk
                    except socket.timeout:
                        print(f"Timeout! Reenviando pedaço {chunk_number}...")
                        chunks.append(packet)


                chunk_number += 1

        # Aguarda solicitações de retransmissão ou encerra se todas forem enviadas
        for chunk in chunks:
            server_socket.settimeout(None)  # Timeout
            server_socket.sendto(chunk, client_address)
            print(f"Reenviando pedaço {chunk_number} com {len(chunk_data)} bytes.")
            # Wait for acknowledgment (ACK)
            ack, _ = server_socket.recvfrom(1024)
            if ack.decode('utf-8') == f"ACK {chunk_number}":
                break  # Move to the next chunk


    except FileNotFoundError:
        error_message = f"ERROR Arquivo {file_name} não encontrado"
        server_socket.sendto(error_message.encode('utf-8'), client_address)
        print(error_message)

def start_server():
    server_socket = create_socket()

    while True:
        data, client_address = server_socket.recvfrom(1024)
        request = data.decode('utf-8').strip()
        if request.startswith("GET"):
            file_name = request.split(' ')[1][1:]
            send_file(file_name, client_address, server_socket)
        else:
            print(f"Requisição inválida: {request}")
            server_socket.sendto(f'ERROR requisição inválida'.encode('utf-8'), client_address)

if __name__ == "__main__":
    start_server()
