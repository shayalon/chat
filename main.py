import socket
from threading import Thread

"""
Author: Shay Alon
version: 18/5/2021
"""
# Finals:
ROOMS_MAX = 10  # number of rooms allowed 10
PARTI_MAX = 100  # number of participants allowed
LOCAL_HOST_IP = '127.0.0.1'
PORT = 55555
MAIN_ROOM_NAME = 'Lobby'

print(f"Runs on LOCAL HOST ip: {LOCAL_HOST_IP} | Entry Port: {PORT}")


class Server:
    """
    A class that represents a thread chat server control.
     responsible to thread new clients, management chats rooms,
     clients corresponding, clients commends, connections
     and organize message protocols
    """

    def __init__(self):
        self.clients = []  # client dict structure -> {"nickname" : nickname, "room" : room , "socket" : socket}
        self.rooms = [MAIN_ROOM_NAME]
        self.HOST = LOCAL_HOST_IP  # local host $$$$$
        self.PORT = PORT
        # establishes new server socket, [(socket.AF_INET -> for IPv6),(socket.SOCK_STREAM -> for TCP)]:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # assigns the current system IP address and a PORT to a socket instance
        self.server.bind((self.HOST, self.PORT))
        self.server.listen()

    def thread_incoming_connections(self):
        """
        The thread_incoming_connections func is a looped method that listening to the sockets
        in port:PORT(final), handling new entering connection and 'threading' it.

        """
        print("Waiting for new connections....  ")
        while True:  # while loop - for always ready to get a new connection
            connection, address = self.server.accept()
            """
            (!)self.accept' method of the server socket waiting for a client connection 
            request given a tuple presenting a socket  => 'connection' and address='address' 
            """
            try:
                while True:
                    if len(self.clients) >= PARTI_MAX:
                        connection.send("0".encode())
                        continue
                    else:
                        connection.send("1".encode())
                    nickname = connection.recv(10).decode()  # get the nickname from the client
                    print(f"get a request from {address}, Nickname: {nickname}")  # notify the server for a new request
                    for client in self.clients:
                        if client['nickname'] == nickname:  # checks that nickname is available
                            print(f"Nickname {nickname}, Taken")
                            connection.send("0".encode())  # if not available send a false response  to the client
                            break
                        continue
                    else:
                        connection.send("1".encode())  # if name available sends a True response to the client
                        client = {"nickname": nickname, "room": MAIN_ROOM_NAME, "socket": connection}
                        # add new client as a dict in a client the list:
                        self.clients.append(client)
                        client['socket'].send(self.rooms[0].encode())
                        print(f'{nickname}, Nickname Valid!...')  # notification on the server the a new client added

                        # Broadcast to main room ('Lobby') for a new chat participant (message type num -[6])
                        msg_content = f"{client['nickname']}, Just logged in..., Find him in Room -  |{client['room']}|"
                        msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
                        self.broadcast(msg, client['room'], client['socket'])
                        break

                # threading new client
                rcv_thread = Thread(target=lambda: self.receive(client))
                rcv_thread.start()

            except (ConnectionResetError, ConnectionAbortedError):
                print("[ERROR] Client was Disconnected")

    def broadcast(self, msg, room, sock):
        """
        this method gets a string argument [msg] representing a message to broadcast,
        a string [room] specify the chat room to send the message to,
        and a client socket [sock], that the message is not relevant

        :param msg: string -message to broadcast
        :param room: string - room to broad cast
        :param sock: socket - skip message in a socket
        """
        for client in self.clients:
            if client['socket'] == sock:
                continue
            if client['room'] == room:
                client['socket'].send(msg.encode())

    def create_room(self, room_name):
        """
        method checks if number of rooms not exceed ROOMS_MAX
        and checks if requested room name doesn't exists in self.rooms (list)

        :param room_name: string -  given room name
        :return: bool
        """
        if len(self.rooms) < ROOMS_MAX and room_name not in self.rooms:
            self.rooms.append(room_name)
            return True
        return False

    def join_room(self, room_name, client_socket):  # client request to join a chat room
        """
        method checks if room name given argument is exists
        if True:
        -> resigning a client from self.clients list in the requested room
        -> broadcast to previous room participants, notify that client has left the room
        -> broadcast to joined room participants, notify that client has joined the room

        (!) broadcast to clients protocol message type num -[6] - participant & room movements

        :param room_name: string - given room name
        :param client_socket: socket - joining client socket
        :return: bool
        """
        for client in self.clients:
            if (client['socket'] == client_socket) and (room_name in self.rooms):
                msg_content = f"{client['nickname']}, Left Room {client['room']}"
                msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
                self.broadcast(msg, client['room'], client['socket'])

                client['room'] = room_name

                msg_content = f"{client['nickname']}, Joined Room {client['room']}"
                msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
                self.broadcast(msg, client['room'], client['socket'])
                return True
        return False

    def remove_room(self, room_name, client_socket):  # client request to delete a chat room
        """
        method checks if room name given argument is not the main room ('Lobby')
        and checks if there are no participant in the room
        if True:
        -> response a notification to the client an invalid option operator and a reason
        if False:
        -> remove room from list and notify
        -> broadcast to room participants, notify that a room was removed
        ->-> response a notification to the client that the room was successfully removed

        (!) broadcast to clients protocol message type num -[6] - participant & room movements

        :param room_name: string -  room name to remove
        :param client_socket: socket - client request socket
        :return: bool

        """
        for client in self.clients:
            if room_name == self.rooms[0]:
                msg_content = f"You Cannot Remove the Main Room |{self.rooms[0]}|"
                msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
                client_socket.send(msg.encode())
                return False

            if client['room'] == room_name:
                msg_content = f"You Cannot Remove Room |{room_name}|, While There's an active participant in the room"
                msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
                client_socket.send(msg.encode())
                return False
        else:
            self.rooms.remove(room_name)
            msg_content = f"Room |{room_name}|, Was Removed"
            msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
            self.broadcast(msg, self.rooms[0], client_socket)
            return True

    def remove_client(self, client):  # responsible for removing disconnected clients
        """
        method gets an dict client argument [client]
        and remove it from the self.client (list) attribute +  closing its socket

        -> broadcast to room participants, notify that client Disconnected from chat

        (!) broadcast to clients protocol message type num -[6] - participant & room movements

        :param client: dict client to remove
        """
        print(f"{client['nickname']}, Disconnected")  # prompt the the server that client is 'no more'
        for connect in self.clients:
            if connect['socket'] == client['socket']:
                self.clients.remove(connect)
        msg_content = f"{client['nickname']}, Disconnected.. "
        msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
        self.broadcast(msg, client['room'], client['socket'])
        client['socket'].close()

    def room_status_msg_builder(self):
        """
        self.room_status_msg_builder() - methods collect all rooms names in self.room attribute
        return a type protocol message [5] for sending it to client

        (!) broadcast to clients protocol message type num -[5] - open rooms

        :return: string
        """
        rooms = ""
        rooms_count = 0
        for room in self.rooms:
            rooms_count += 1
            rooms += room + "&&&"
        return f"{5}{str(len(rooms)).zfill(4)}{rooms}"

    def receive(self, client):
        """
        The receive func is a 'threaded' looped method that listening to the clients,
        waiting to gets a protocol type message from a 'thread'
        by the protocol number first message char the methods knows how to redirect a message
        or operate a command from the client;

        type message protocols [msgType] from client:
        msgType = 2 -> join a room request"
        msgType = 3 -> exit a room request"
        msgType = 4 -> generate new room request"
        msgType = 5 -> delete a room request"
        msgType = 6 -> broadcast a message request"
        msgType = 7 -> get room participants info request"
        msgType = 8 -> get all rooms status info request"

        :param client: dict client
        """
        while True:
            try:
                # message protocol:
                msgType = int(client['socket'].recv(1).decode())

                if not 0 < msgType < 9:  # if not follow protocol client will disconnect!
                    print("not valid Protocol number")
                    self.remove_client(client)

                msgLen = client['socket'].recv(4).decode()
                msgContent = client['socket'].recv(int(msgLen)).decode()

                if msgType == 2:  # massage type num-2 = join a room
                    print("! Received message protocol [NUM 2] -> join a room request")
                    # first send update of rooms status to the client:
                    msg = self.room_status_msg_builder()
                    client['socket'].send(msg.encode())

                    if self.join_room(msgContent, client['socket']):
                        msg = f"{2}1{str(msgLen).zfill(4)}{msgContent}"
                        print("entered a room")
                    else:
                        msg = f"{2}0{str(msgLen).zfill(4)}{msgContent}"
                        print("not entered a room")
                    client['socket'].send(msg.encode())

                if msgType == 3:  # user exit the room
                    print("! Received message protocol [NUM 3] -> exit room request")
                    if client['room'] == self.rooms[0]:  # do noting if its lobby room
                        pass
                    else:
                        msg_content = f"{client['nickname']}, Left Room {client['room']}"
                        msg = f"{6}{str(len(msg_content)).zfill(4)}{msg_content}"
                        self.broadcast(msg, client['room'], client['socket'])
                        client['room'] = self.rooms[0]

                if msgType == 4:
                    print("! Received message protocol [NUM 4] -> generate a room request")
                    if self.create_room(msgContent):
                        print(f"! Generate a room name: {msgContent} request granted!")
                        msg = f"{3}1{str(msgLen).zfill(4)}{msgContent}"
                    else:
                        print(f"! Failed to Generate a room: {msgContent}!")
                        msg = f"{3}0{str(msgLen).zfill(4)}{msgContent}"
                    client['socket'].send(msg.encode())
                    print(msg)

                if msgType == 5:  # delete a room
                    print("! Received message protocol [NUM 5] -> delete a room request")
                    # first send update of rooms status to the client:

                    if self.remove_room(msgContent, client['socket']):
                        msg = f"{7}1{str(msgLen).zfill(4)}{msgContent}"
                        print("Room Removed")
                    else:
                        msg = f"{7}0{str(msgLen).zfill(4)}{msgContent}"
                        print(f"Failed to remove room {msgContent}")
                    client['socket'].send(msg.encode())

                # message from client:
                if msgType == 6:
                    print("! Received message protocol [NUM 6] -> broadcast a message request")
                    msg = f"{1}{str(msgLen).zfill(4)}{len(client['nickname'])}{client['nickname']}{msgContent}"
                    print("Broadcast pack: ", msg)
                    # send a the message to the clients current room:
                    self.broadcast(msg, client['room'], client['socket'])

                if msgType == 7:  # return the client current room participants
                    print("! Received message protocol [NUM 7] -> room participants info request")
                    parti = client['room']
                    for part in self.clients:
                        if part['room'] == client['room']:
                            parti += "&&&" + part['nickname']
                    msg = f"{4}{str(len(parti)).zfill(4)}{parti}"
                    print(msg)
                    client['socket'].send(msg.encode())

                if msgType == 8:  # rooms status ,in used and available rooms
                    print("! Received message protocol [NUM 8] -> room status info request")
                    msg = self.room_status_msg_builder()
                    print(msg)
                    client['socket'].send(msg.encode())

            # if gets error remove the client from the clients list and close his the socket:
            except (ConnectionResetError, ConnectionAbortedError):
                print("[ERROR] Client was Disconnected")
                self.remove_client(client)
                break


# run server:
server = Server()
server.thread_incoming_connections()