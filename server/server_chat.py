from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time
from person import Person

buffer_size = 512
host = '127.0.0.1'
port = 8888
address = (host,port)
server = socket(AF_INET, SOCK_STREAM)
server.bind(address)
max_connections = 10

persons = []

def broadcast(message,name):
    for person in persons:
        client = person.client
        client.send(bytes(name,"utf8")+message)
        
    


def client_communication(person):
    
    client = person.client
    
    name = client.recv(buffer_size).decode("utf8")
    person.set_name(name)
    print(name)
    msg = bytes(f"{name} has joined the chat!","utf8")
    broadcast(msg,"")
    
    while True:
        try:
            msg = client.recv(buffer_size)
            if msg == bytes("{quit}","utf8"):
                client.send(bytes("{quit}","utf8"))
                client.close()
                persons.remove(person)
                broadcast(bytes(f"{name} has left the chat...", "utf8"), "")
                print(f"[DISCONNECTED] {name} disconnected")
                break
            else:
                broadcast(msg,name+": ")
                print(f"{name}: ",msg.decode("utf8"))
        except Exception as e:
            print("[EXCEPTION]xsxsxsxsx",e)
            break
            
        
        

def wait_for_connection():
    run = True
    while run:
        try:
            client,address = server.accept()
            person = Person(address,client) 
            persons.append(person)
            print(persons)
            print(f"[Connection] {address} connected to the server at {time.time()}")
            Thread(target = client_communication,args=(person,)).start()
        except Exception as e:
            print("[EXCEPTION]swswswsws",e)
            run = False
            break
    
    print("Server Crashed!")
            


if __name__ == '__main__':
    server.listen(max_connections)
    print("Waiting for connection...")
    accept_thread = Thread(target = wait_for_connection)
    accept_thread.start()
    accept_thread.join()
    server.close()