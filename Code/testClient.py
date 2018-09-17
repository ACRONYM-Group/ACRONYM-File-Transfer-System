import socket
import dataOverStream as DataStream
import keyExchange

import encryption

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clientSocket.connect(("127.0.0.1", 4242))

data = list(clientSocket.recv(1024))

def sendEncrypted(conn, data, key):
    with DataStream.DataStreamOut(conn) as stream:
        stream.sendData(DataStream.DATA_TYPE_STRING, encryption.encrypt(data, key))

def readEncrypted(conn, key):
    with DataStream.DataStreamIn(conn) as stream:
        data = stream.getData(DataStream.DATA_TYPE_STRING)
        return encryption.decrypt(data, key)

clientSocket.sendall(bytearray([3,1,4,1,5]))

with DataStream.DataStreamIn(clientSocket) as stream:
    prime1 = stream.getData(DataStream.DATA_TYPE_LONG)
    prime2 = stream.getData(DataStream.DATA_TYPE_LONG)
    otherMixed = stream.getData(DataStream.DATA_TYPE_LONG)
exchange = keyExchange.KeyExchange((prime1, prime2))
exchange.randomSecret()

with DataStream.DataStreamOut(clientSocket) as stream:
    mixed = exchange.calculateMixed()
    stream.sendData(DataStream.DATA_TYPE_LONG, int(mixed))

key = exchange.getSharedKey(otherMixed)

print ("Settled Key: " + str(key))

sendEncrypted(clientSocket, "LOGIN", key)
readEncrypted(clientSocket, key)
sendEncrypted(clientSocket, "Username", key)
readEncrypted(clientSocket, key)
sendEncrypted(clientSocket, "Password", key)