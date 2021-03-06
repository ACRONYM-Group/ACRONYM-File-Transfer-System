import sys
print(sys.executable)

import socket
import threading

import keyExchange
import errno

import primes as Primes
import dataOverStream as DataStream

import encryption
import re

import packet as Packet
import dataOverString as DataString

import time
import json

import platform
import os

import base64
import math

from datetime import datetime
from datetime import timedelta

import hashlib
import subprocess

import AccountHandler

import ServerLibraryActions


programStartTime = datetime.now()
OSName = platform.platform()

programInstallDirectory = "/home/acronym/amps/"

AccountHandler.DATA_FILE_PATH = programInstallDirectory + "\\data\\data.json"
AccountHandler.import_data()

AccountHandler.export_data()

users_data = None
packages_data = None
computers_data = None

server_socket = None

port = 4242
host_name = ""

global_cache = {}
file_write_queue = {}

MOTD = "I thought this was depricated?!"

alert_subscriptions = {}

print(" ")
print("AMPS Starting Up...")
print("====================")
print("Current AMPS Software Version: 2019.2.7.1")
print("Current Software Platform: " + OSName)
print(" ")

#ServerLibraryActions.execute("RCON", "connect", {"address":"127.0.0.1", "password":"password"})

def check_user_passhash(username, password_hash):
    return True
    SUCCESS = AccountHandler.enums.LOGIN_SUCCESSFUL
    result = AccountHandler.check_credentials(username, password_hash)
    if result == SUCCESS:
        return True

    return False


def read_data_files():
    global users_data
    global packages_data
    global computers_data
    
    try:
        with open(programInstallDirectory + "Data/users.json","r") as f:
            contents = f.read()
        users_data = json.loads(contents)
        print("Successfully loaded data for " + str(len(users_data)) + " Users...")

    except Exception as error:
        print("FAILED TO LOAD USER DATA!")
        print(error)

    try:
        with open(programInstallDirectory + "Data/packages.json","r") as f:
            contents = f.read()
        packages_data = json.loads(contents)
        print("Successfully loaded data for " + str(len(packages_data)) + " Packages...")

    except Exception as error:
        print("FAILED TO LOAD PACKAGE DATA!")
        print(error)

    try:
        with open(programInstallDirectory + "Data/computers.json","r") as f:
            contents = f.read()
        computers_data = json.loads(contents)
        print("Successfully loaded data for " + str(len(computers_data)) + " Computers...")

    except Exception as error:
        print("FAILED TO LOAD COMPUTER DATA!")
        print(error)
     

def initalize_connection():
    global server_socket

    print("Connecting to address " + str(host_name) + ":" + str(port))
      
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host_name, port))


def dump_data():
    f = open(programInstallDirectory + "Data/users.json", "w")
    f.write(json.dumps(users_data))
    
    f = open(programInstallDirectory + "Data/computers.json", "w")
    f.write(json.dumps(computers_data))
    
    f = open(programInstallDirectory + "Data/packages.json", "w")
    f.write(json.dumps(packages_data))

def file_download_process(self, packet, isPackage=False, shouldIncludeFinalFolder=True):
    file_name = packet["data"]["filePath"]
    actual_file_name = os.path.basename(file_name)

    if programInstallDirectory in packet["data"]["filePath"]:
        lengthInstallDir = len(programInstallDirectory)
    else:
        lengthInstallDir = 3

    filePathToSend = packet["data"]["filePath"][lengthInstallDir:]
    print(filePathToSend)
    
    if isPackage:
        filePathModifier = filePathToSend[:-len(actual_file_name)]
        if not shouldIncludeFinalFolder:
            filePathModifier = os.path.dirname(os.path.dirname(filePathModifier)) + "/"
    else:
        filePathModifier = ""

    data_to_send = encryption.encrypt(json.dumps({"CMDType":"sftpFileDownload", "payload":{"FilePathRead":packet["data"]["filePath"], "filePathWrite": filePathToSend, "fileName": actual_file_name, "filePathModifier":filePathModifier}}), self.shared_key)
    Packet.Packet(data_to_send, "__CMD__").send(self.connection, packet["data"]["windowID"])

def file_download_processOLD(self, packet, isPackage=False, shouldIncludeFinalFolder=True):
    print("Starting file download")
    if isPackage:
        shouldIncludeFinalFolder = False
    file_name = packet["data"]["filePath"]
    actual_file_name = os.path.basename(file_name)
    file_object = open(file_name, 'rb')

    file_data = file_object.read()
    file_length = len(file_data)
    index = 0
    packet_index = 0

    if programInstallDirectory in packet["data"]["filePath"]:
        lengthInstallDir = len(programInstallDirectory)
    else:
        lengthInstallDir = 3

    filePathToSend = packet["data"]["filePath"][lengthInstallDir:]
    print(filePathToSend)
    if isPackage:
        filePathModifier = filePathToSend[:-len(actual_file_name)]
        print("File Path Modifier: " + filePathModifier)
        if not shouldIncludeFinalFolder:
            print("Basename: " + os.path.dirname(os.path.dirname(filePathModifier)))
            filePathModifier = os.path.dirname(os.path.dirname(filePathModifier)) + "/"
            print("File Path Modifier: " + filePathModifier)
    else:
        filePathModifier = ""

    print(actual_file_name)
    
    while len(file_data) > 2000000:
        current_chunk = file_data[:2000000]

        fileDataB64 = base64.b64encode(current_chunk).decode("ascii")
        if programInstallDirectory in packet["data"]["filePath"]:
            lengthInstallDir = len(programInstallDirectory)
        else:
            lengthInstallDir = 3

        filePathToSend = packet["data"]["filePath"][lengthInstallDir:]
        print(filePathToSend)
        if isPackage:
            filePathModifier = filePathToSend[:-len(actual_file_name)]
            if not shouldIncludeFinalFolder:
                filePathModifier = os.path.dirname(os.path.dirname(filePathModifier)) + "/"
        else:
            filePathModifier = ""


        
        data_to_send = encryption.encrypt(json.dumps({"CMDType":"downloadFileChunk", "payload":{"file":fileDataB64, "index": index, "packetIndex": packet_index, "length": file_length, "filePath": filePathToSend, "fileName": actual_file_name, "filePathModifier":filePathModifier, "windowID":packet["data"]["windowID"]}}), self.shared_key)
        
        Packet.Packet(data_to_send, "__CMD__").send(self.connection, packet["data"]["windowID"])
        
        index += 2000000
        packet_index += 1

        file_data = file_data[2000000:]
        
    current_chunk = file_data[:]
    fileDataB64 = base64.b64encode(current_chunk).decode("ascii")
    data_to_send = encryption.encrypt(json.dumps({"CMDType":"downloadFileChunk", "payload":{"file":fileDataB64, "index": index, "packetIndex": packet_index, "length": file_length, "filePath":filePathToSend, "fileName": actual_file_name, "filePathModifier":filePathModifier, "windowID":packet["data"]["windowID"]}}), self.shared_key)
    
    Packet.Packet(data_to_send, "__CMD__").send(self.connection, packet["data"]["windowID"])

    data_to_send = encryption.encrypt(json.dumps({"CMDType":"fileTransferComplete", "payload": {"fileName":actual_file_name, "finalPacketIndex":packet_index, "filePathModifier":filePathModifier}}), self.shared_key)
    Packet.Packet(data_to_send, "__CMD__").send(self.connection, packet["data"]["windowID"])

    
def get_ver_part(version, part):
    versionParts = version.split(".")
    if part == "major":
        return int(versionParts[0])

    if part == "minor":
        return int(versionParts[1])

    if part == "patch":
        return int(versionParts[2])

    
def compare_greater_version(firstVersion, secondVersion):
    if get_ver_part(firstVersion, "major") > get_ver_part(secondVersion, "major"):
        return True
    elif get_ver_part(firstVersion, "major") == get_ver_part(secondVersion, "major"):
        if get_ver_part(firstVersion, "minor") > get_ver_part(secondVersion, "minor"):
            return True
        elif get_ver_part(firstVersion, "minor") == get_ver_part(secondVersion, "minor"):
            if get_ver_part(firstVersion, "patch") > get_ver_part(secondVersion, "patch"):
                return True
            else:
                return False
        else:
            return False
    else:
        return False

    
def get_highest_version(verList, specificMajor=-1):
    highest = "0.0.0"
    for s in verList:
        if specificMajor == -1 or get_ver_part(s, "major") == specificMajor:
            if get_ver_part(s, "major") > get_ver_part(highest, "major"):
                highest = s
            
            if get_ver_part(s, "major") == get_ver_part(highest, "major"):
                if get_ver_part(s, "minor") > get_ver_part(highest, "minor"):
                    highest = s
                
                if get_ver_part(s, "minor") == get_ver_part(highest, "minor"):
                    if get_ver_part(s, "patch") > get_ver_part(highest, "patch"):
                        highest = s

    return highest


def subscribe_to_data_changes(data_title, connection):
    global alert_subscriptions
    
    if data_title in alert_subscriptions:
        alert_subscriptions[data_title].append(connection)
    else:
        alert_subscriptions[data_title] = [connection]

def remove_subscription(connection):
    print("Removing Connection " + str(connection.address))
    for key in alert_subscriptions:
        if connection in alert_subscriptions[key]:
            alert_subscriptions[key].remove(connection)

    
class ClientConnection:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address

        self.packet_recieve_generator = Packet.fullGenerator(self.connection)

        self.shared_key = None
        self.authenticated = False

        self.username = ""

    def data_change(self, key, new_value, old_value):
        dataToSend = encryption.encrypt(json.dumps({"CMDType":"dataChange", "payload": {"key":key, "oldValue": old_value, "newValue": new_value}}), self.shared_key)
        Packet.Packet(dataToSend, "__CMD__").send(self.connection)

    def download_directory(self, packet, isPackage=False, packageName=None):
        key = self.shared_key
        dir = packet["data"]["filePath"]

        if os.path.isdir(dir):
            print("Client would like to download " + dir)

            for root, directories, filenames in os.walk(dir):
                for directory in directories:

                    directory_path = os.path.join(root, directory)


                for filename in filenames:
                    print(filename)

                    file_path = os.path.join(root,filename).replace("\\", "/")
                    if not isPackage:
                        filePathModifier = os.path.dirname(file_path)
                        filePathModifier = filePathModifier[len(os.path.dirname(dir))+1:] + "/"
                    else:
                        filePathModifier = ""
                    print(filename)
                    file_download_process(self, {"data":{"filePath":file_path, "windowID":-1, "filePathModifier":packet["data"]["filePathModifier"] + filePathModifier}}, isPackage)
            
            if isPackage:
                dataToSend = encryption.encrypt(json.dumps({"CMDType":"packageDownloadComplete", "payload": {"package":packageName}}), self.shared_key)
                Packet.Packet(dataToSend,"__CMD__").send(self.connection)

        else:
            print("Client is trying to download a nonexistant directory: " + dir)

    def perform_handshake(self):
        Packet.Packet('31415', "__HDS__").send(self.connection)

        data = next(self.packet_recieve_generator)

        if data["payload"] == "31415":
            print ("Handshake with " + str(self.address[0]) + " sucessful!")
            return True
        else:
            print ("Handshake with " + str(self.address[0]) + " failed!")
            print ("Responce Recieved: ")
            print (data)
            return False

    def perform_key_exchange(self):
        primePair = Primes.getPrimePair()
        exchange = keyExchange.KeyExchange(primePair)
        exchange.randomSecret()

        mixed = exchange.calculateMixed()


        Packet.Packet(chr(0) + chr(1) + DataString.convertIntToData(primePair[0]),"__DAT__").send(self.connection)
        time.sleep(0.1)
        Packet.Packet(chr(0) + chr(2) + DataString.convertIntToData(primePair[1]),"__DAT__").send(self.connection)
        time.sleep(0.1)
        Packet.Packet(chr(0) + chr(3) + DataString.convertIntToData(mixed),"__DAT__").send(self.connection)

        packet = next(self.packet_recieve_generator)

        val = DataString.convertDataToInt(packet["payload"][2:])

        self.shared_key = exchange.getSharedKey(val)

    def connection_handler(self):
        try:
            self.perform_handshake()
            self.perform_key_exchange()

            print(self.shared_key)

            while True:
                packet = next(self.packet_recieve_generator)

                #If the packet is a command, it is encrypted, so decrypt that quick
                if packet["packetType"] == "__CMD__":
                    packet = encryption.decrypt(packet["payload"], self.shared_key)
                    packet = "".join(packet)

                    try:
                        packet = json.loads(packet)
                    except TypeError as e:
                        print("Packet Unable to be parsed")
                        print(packet)
                        continue

                self.process_packet(packet)
        except ConnectionResetError:
            self.connection.close()
            remove_subscription(self)
            print("Connection Reset")

    def process_packet(self, packet):
        if isinstance(packet, str):
            print(packet)
            packet = json.loads(packet)

        if packet["CMDType"] == "login":
            try:
                userCredentials = json.loads(packet["data"])
            except TypeError:
                userCredentials = packet["data"]
            
            self.authenticated = check_user_passhash(userCredentials["username"], userCredentials["password"])

            dataToSend = encryption.encrypt(json.dumps({"CMDType":"AuthResult", "data":self.authenticated}), self.shared_key)
            Packet.Packet(dataToSend, "__CMD__").send(self.connection)
            self.username = userCredentials["username"]

            print(self.username + " has attempted to login: " + str(self.authenticated))

        elif packet["CMDType"] == "startMCServer":
            subprocess.Popen(["whoami"])
            subprocess.Popen(["sudo", "/home/acronym/Desktop/MCServer.sh", "&"])
        
        elif packet["CMDType"] == "setData":
            #print("Set Data", packet["name"], "=", packet["value"])
            value = packet["value"]

            if packet["name"] in alert_subscriptions:
                for conn in alert_subscriptions[packet["name"]]:
                    if packet["name"] in global_cache:
                        old = global_cache[packet["name"]]
                    else:
                        old = None
                    conn.data_change(packet["name"], value, old)

            global_cache[packet["name"]] = value

            #print(global_cache)
        
        elif packet["CMDType"] == "getData":
            if packet["name"] in global_cache:
                value = global_cache[packet["name"]]
            else:
                value = ""
            
            data = {"packetType":"__DAT__", "payload":value}
            encr = encryption.encrypt(json.dumps(data), self.shared_key)
            Packet.Packet(encr, "__DAT__").send(self.connection)

        elif packet["CMDType"] == "getDataJS":
            if packet["name"] in global_cache:
                value = global_cache[packet["name"]]
            else:
                value = ""
            
            data = {"packetType":"__CMD__", "CMDType":"getDataResponse", "key":packet["name"], "value":value}
            encr = encryption.encrypt(json.dumps(data), self.shared_key)
            Packet.Packet(encr, "__CMD__").send(self.connection)

        elif packet["CMDType"] == "downloadFile":
            threading.Thread(target=file_download_process, args=(self, packet)).start()

        elif packet["CMDType"] == "uploadFile":
            file_name = packet["data"]["filePath"].replace("\\", "/")
            if not os.path.exists(os.path.dirname(file_name)):
                try:
                    os.makedirs(os.path.dirname(file_name))
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            if not file_name in file_write_queue:
                file_write_queue[file_name] = {"index":0, "outOfOrderPackets":{}, "startTime": datetime.now()}
            if file_write_queue[file_name]["index"] == packet["data"]["index"]:
                if not "fileReference" in file_write_queue[file_name]:
                    file = open(file_name, "wb")
                    file.write(base64.b64decode(packet["data"]["file"]))
                    file.close()
                    file_write_queue[file_name]["fileReference"] = open(file_name, "ab")
                    file_write_queue[file_name]["index"] += 1
                else:
                    file_write_queue[file_name]["fileReference"].write(base64.b64decode(packet["data"]["file"]))
                    file_write_queue[file_name]["index"] += 1
            else:
                file_write_queue[file_name]["outOfOrderPackets"][packet["data"]["index"]] = packet["data"]["file"]

            i = file_write_queue[file_name]["index"] + 1
            hasFoundEmptyPacket = False
            while (i <= 5):
                if i in file_write_queue[file_name]["outOfOrderPackets"] and "fileReference" in file_write_queue[file_name]:
                    if hasFoundEmptyPacket == False:
                        file_write_queue[file_name]["fileReference"].write(base64.b64decode(file_write_queue[file_name]["outOfOrderPackets"][i]))
                        file_write_queue[file_name]["index"] += 1
                else:
                    hasFoundEmptyPacket = True
                i += 1

            if "finalPacketIndex" in file_write_queue[file_name]:
                if file_write_queue[file_name]["finalPacketIndex"] == file_write_queue[file_name]["index"]:
                    print("Write of " + file_name + " Complete! Took " + millis(file_write_queue[file_name]["startTime"]) + " Milliseconds")
                    #fileWriteQueue[commandRec["data"]["filePath"]]["fileReference"].close()
                    #fileWriteQueue[commandRec["data"]["filePath"]] = None

        elif packet["CMDType"] == "requestFiles":
            filesDataToSend = []
            commandData = packet["data"]
            directory = os.listdir(commandData["path"])
            for s in directory:
                fileData = {"name":s, "size":os.stat(packet["data"]["path"] + s).st_size}
                filesDataToSend.append(fileData)
            
            dataToSend = encryption.encrypt(json.dumps({"CMDType":"updateFiles", "data":{"files":filesDataToSend, "window":commandData["windowID"], "path": packet["data"]["path"]}}), self.shared_key)
            Packet.Packet(dataToSend, "__CMD__").send(self.connection)

        elif packet["CMDType"] == "requestMOTD":
            print("Sending the client the MOTD")
            dataToSend = encryption.encrypt(json.dumps({"CMDType":"updateMOTD", "data":MOTD}), self.shared_key)
            dataToSendDecrypt = encryption.decrypt(dataToSend, key)
            Packet.Packet(dataToSend, "__CMD__").send(self.connection)

        elif packet["CMDType"] == "uploadFileFinish":
            packet["data"]["filePath"] = packet["data"]["filePath"].replace("\\", "/")
            if file_write_queue[packet["data"]["filePath"]]["index"] >= packet["data"]["finalPacketIndex"]:
                file_write_queue[packet["data"]["filePath"]]["fileReference"].close()
                file_write_queue[packet["data"]["filePath"]] = None
            else:
                file_write_queue[packet["data"]["filePath"]]["finalPacketIndex"] = packet["data"]["finalPacketIndex"]

        elif packet["CMDType"] == "downloadDir":
            self.download_directory(packet)

        elif packet["CMDType"] == "downloadPackage":
            packet["data"] = json.loads(packet["data"])
            self.download_directory({"data":{"filePathModifier":packages_data[packet["data"]["package"]]["dataDir"], "filePath":programInstallDirectory[:-1] + packages_data[packet["data"]["package"]]["dataDir"] + packet["data"]["version"]}}, True, packet["data"]["package"])
            if not packet["data"]["package"] in computers_data[packet["data"]["computerName"]]["subbedPackages"]:
                computers_data[packet["data"]["computerName"]]["subbedPackages"][packet["data"]["package"]] = {"specificMajor":-1}
            computers_data[packet["data"]["computerName"]]["subbedPackages"][packet["data"]["package"]]["version"] = packet["data"]["version"]
            dump_data()

        elif packet["CMDType"] == "requestUserData":
                print("Sending a User Their User Data!")
                dataToSend = encryption.encrypt(json.dumps({"CMDType":"userData", "data":{"userData":{"username":users_data[self.username]["username"], "statusCardSubs":users_data[self.username]["statusCardSubs"]}, "computerData":computers_data[packet["computerName"]] }}), self.shared_key)
                Packet.Packet(dataToSend, "__CMD__").send(self.connection)

        elif packet["CMDType"] == "downloadPackageList":
            print("Client is requesting Package List")
            dataToSend = encryption.encrypt(json.dumps({"CMDType":"avaliablePackages", "data":packages_data}), self.shared_key)
            Packet.Packet(dataToSend,"__CMD__").send(self.connection)

        elif packet["CMDType"] == "sendNotification":
            print(" ")
            print("Broadcasting Notification: ")
            print(packet["data"]["notification"]["subject"])
            print(packet["data"]["notification"]["body"])
            
        elif packet["CMDType"] == "requestInstallationDir":
            dataToSend = encryption.encrypt(json.dumps({"CMDType":"installationDir", "data":programInstallDirectory}), self.shared_key)
            Packet.Packet(dataToSend,"__CMD__").send(self.connection)

        elif packet["CMDType"] == "deletePackage":
            print("DELETING Package")
            print(packet["data"]["package"])
            del packages_data[packet["data"]["package"]]
            dump_data()

        elif packet["CMDType"] == "uploadNewPackage":
            print("Uploading New Package")
            packages_data[packet["data"]["package"]] = {"desc":packet["data"]["packageDesc"], "dataDir":"/Data/Packages/" + packet["data"]["package"] + "/",  "versions":{packet["data"]["newVersionNumber"]:{}}, "defaultVersion":packet["data"]["newVersionNumber"]}
            dump_data() 

        elif packet["CMDType"] == "uploadNewVersion":
            print("Uploading New Package Version")
            packages_data[packet["data"]["package"]]["versions"][packet["data"]["newVersionNumber"]] = {}
            dump_data()

        elif packet["CMDType"] == "updatePackageDefaultVersion":
            print("Updating Package Default Version")
            packages_data[packet["data"]["package"]]["defaultVersion"] = packet["data"]["newDefaultVersion"]
            dump_data()

        elif packet["CMDType"] == "updateSubbedPackages":
            computers_data[json.loads(packet["data"])["computerName"]]["subbedPackages"] = json.loads(packet["data"])["subbedPackages"]
            dump_data()

        elif packet["CMDType"] == "installPackage":
            packet["data"] = json.loads(packet["data"])
            computers_data[packet["data"]["computerName"]]["subbedPackages"][packet["data"]["package"]] = {"specificMajor":-1, "version":"0.0.0"}
            dump_data()

        elif packet["CMDType"] == "checkForPackageUpdates":
            packagesToUpdate = {}
            index = 0
            for s in computers_data[packet["data"]["computerName"]]["subbedPackages"]:
                try:
                    usersCurrentVersion = computers_data[packet["data"]["computerName"]]["subbedPackages"][s]["version"]
                    usersSpecificMajor = computers_data[packet["data"]["computerName"]]["subbedPackages"][s]["specificMajor"]
                    highestVersion = get_highest_version(packages_data[s]["versions"], computers_data[packet["data"]["computerName"]]["subbedPackages"][s]["specificMajor"])
                    print("Checking " + str(s) + " for updates. user: " + str(usersCurrentVersion) + " specificMajor: " + str(usersSpecificMajor) + " highest: " + str(highestVersion))
                    print(compare_greater_version(highestVersion, usersCurrentVersion))
                    if compare_greater_version(highestVersion, usersCurrentVersion):
                        print("     Found updated version!")
                        packagesToUpdate[index] = {"package":s, "currentVersion":usersCurrentVersion, "newVersion":highestVersion}
                        index = index + 1
                except:
                    print("Unable to check updates for " + s + " moving on.")
                    
            if len(packagesToUpdate) > -1:
                dataToSend = encryption.encrypt(json.dumps({"CMDType":"avaliablePackageUpdates", "data":packagesToUpdate}), self.shared_key)
                Packet.Packet(dataToSend,"__CMD__").send(self.connection)
            
        elif packet["CMDType"] == "subscribeToEvent":
            print(self.address, "is subscribing to the key", packet["data"]["dataTitle"])
            data_title = packet["data"]["dataTitle"]
            subscribe_to_data_changes(data_title, self)

        elif packet["CMDType"] == "libraryFunction":
            ServerLibraryActions.execute(packet["data"]["library"], packet["data"]["function"], packet["data"]["arguments"])

def listener():
    while True:
        server_socket.listen(1)
        conn, addr = server_socket.accept()

        connection = ClientConnection(conn, addr)
        threading.Thread(target=connection.connection_handler, args=()).start()


def start_listener():
    threading.Thread(target=listener, args=()).start()
       
if __name__ == "__main__":
    read_data_files()
    initalize_connection()

    start_listener()
