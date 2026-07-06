import socket
import threading
import sqlite3
import os
from queue import Queue
from dotenv import load_dotenv 

# Carrega as variáveis do arquivo .env
load_dotenv()

# Agora com o os.getenv() para buscar as configs ou usar um valor padrão
ALVO = os.getenv("ALVO")
THREADS_LIMIT = int(os.getenv("THREADS_LIMIT"))
DB_NAME = os.getenv("DB_NAME")

fila = Queue()
conexao = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conexao.cursor()

def tentar_capturar_banner(investigador):
    try:
        investigador.send(b"HEAD / HTTP/1.1\r\n\r\n")
        return investigador.recv(1024).decode().split('\r\n')[0]
    except OSError:
        return "Desconhecido"

def trabalhador():
    while not fila.empty():
        porta = fila.get()
        investigador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        investigador.settimeout(0.5)
        
        if investigador.connect_ex((ALVO, porta)) == 0:
            banner = tentar_capturar_banner(investigador)
            print(f"[+] Porta {porta} ABERTA | Serviço: {banner}")
            cursor.execute("INSERT INTO resultados VALUES (?, 'ABERTA', ?, CURRENT_TIMESTAMP)", (porta, banner))
            conexao.commit()
            
        investigador.close()
        fila.task_done()

for porta in range(1, 1025):
    fila.put(porta)

for _ in range(THREADS_LIMIT):
    t = threading.Thread(target=trabalhador)
    t.start()