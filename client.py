import socket
from threading import Thread

"""
Author: Shay Alon
version: 18/5/2021
"""

LOCAL_HOST_IP = '127.0.0.1'
PORT = 55555
NICKNAME_MAX_LEN = 10
MESSAGE_MAX_LEN = 90

print(f"Runs on LOCAL HOST ip: {LOCAL_HOST_IP} | Entry Port: {PORT}\nWaiting for server...\n\n")


class Client:
    """
    A class that represents a thread chat client
    ask for a threaded 'connection' from the server,
    listening to the server for protocols and messages
    send commands to server and handles server feedbacks
    corresponding (send and receive chats messages)
    and organize server message protocols
    """

    def __init__(self):
        # establishes new client socket, [(socket.AF_INET -> for IPv6),(socket.SOCK_STREAM -> for TCP)]:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = None  # client instance nickname attribute
        self.room = None  # client instance current room attribute
        self.rooms_list = []  # server available rooms - for using attribute needs an server update!

    def send_roope_and_thread(self):
        """
        send to the server a connection request,
        sends tto the server requested nickname and wit for a approval or decline,
        thread 'send' and 'receive' methods

        :return: None
        """
        try:
            self.client.connect((LOCAL_HOST_IP, PORT))
            # ^LOCAL_HOST_IP, PORT ^ -> are final arguments for Approaching the server:
            # ask from the user his nickname and send it to the server:
            while True:
                max_check = bool(int(self.client.recv(1).decode()))
                if not max_check:
                    print("Sorry chats rooms are full!, Try again later")
                    self.client.close()
                    input("Press any key to Exit!...")
                    exit()
                user_nickname = input("Enter Your Nickname: \n")  # when connecting ask for nickname:
                if len(user_nickname) > NICKNAME_MAX_LEN:  # checks name len
                    print(f"User Nickname should be no more the {NICKNAME_MAX_LEN} characters!\n")
                    continue

                self.client.send(user_nickname.encode())  # send requested nickname for the sever confirmation
                print("sending request to the server")
                name_check = bool(int(self.client.recv(1).decode()))
                print(f"get a answer from the server : {name_check}\n")

                if name_check:
                    self.nickname = user_nickname
                    self.room = self.client.recv(10).decode()
                    # self.client.send(self.nickname.encode())
                    print(f" Hey {self.nickname}, Welcome to the chat :-) ".center(50, "~"))
                    print(f"Your current room is:  {self.room}")
                    print("\nFor menu press 'M'/'m\', press 'exit' to exit room")
                    print("Enter your massage:\n")
                    break
                else:
                    print(f"Sorry the user name {user_nickname} is already taken!")
                    continue

            # threading receive and send (broadcast) Methods
            receive_thread = Thread(target=self.receive)
            receive_thread.start()

            send_thread = Thread(target=self.send)
            send_thread.start()
        except ConnectionRefusedError:
            print("[ERROR] SORRY SOMETHING WENT WRONG WITH THE SERVER!, You where Disconnected !")


    def receive(self):
        """
        The receive func is a 'threaded' looped method that listening to the server,
        waiting to gets a protocol type message and decode it
        by the protocol number first message char the methods knows how to redirect a message
        or operate a command from the server;

        type message protocols [msgType] from server:
        msgType = 1 -> incoming message includes sender nickname
        msgType = 2 -> response to a client joining room request - gets bool and room name
        msgType = 3 -> client generate new room request server response -  gets bool and room name
        msgType = 4 -> current room participants info server response - gets a string representing all participants
        msgType = 5 -> current available rooms and update [self.rooms_list] instance attribute
        msgType = 6 -> gets info of a participant movements ('if someone joined/left the chat room')
        msgType = 7 -> server respond to remove a room, client request - gets bool
        """
        try:
            while True:
                # message protocol:

                # Received message protocol [NUM 3] from server -> get a broadcast message
                msgType = int(self.client.recv(1).decode())
                if msgType == 1:  # get message and sender nickname and prints content
                    msgLen = int(self.client.recv(4).decode())
                    nickNameLen = int(self.client.recv(1).decode())
                    nickname = self.client.recv(nickNameLen).decode()
                    msgContent = self.client.recv(msgLen).decode()
                    print("\n" + nickname + ": " + msgContent)
                # Received message protocol [NUM 3] from server -> entering a room request
                if msgType == 2:
                    RoomEnteredBool = bool(int(self.client.recv(1).decode()))
                    roomNameLen = int(self.client.recv(4).decode())
                    roomName = self.client.recv(roomNameLen).decode()
                    if RoomEnteredBool:  # user feed back for server approval or decline:
                        print(f"Welcome to Room {roomName}!")
                    else:
                        print(f"Failed to enter Room: {roomName}!")
                # Received message protocol [NUM 3] from server -> generate a room request
                if msgType == 3:
                    RoomCreatedBool = bool(int(self.client.recv(1).decode()))
                    roomNameLen = int(self.client.recv(4).decode())
                    roomName = self.client.recv(roomNameLen).decode()
                    if RoomCreatedBool:  # user feed back for server approval or decline:
                        print(f"Room {roomName} was Created!")
                    else:
                        print(f"Failed to Create Room {roomName}\nCheck if given room name exist or "
                              f"exceed number rooms allowed")
                # Received message protocol [NUM 4] from server -> current room participants info
                if msgType == 4:
                    parti_len = int(self.client.recv(4).decode())
                    parti_str = self.client.recv(parti_len).decode()
                    parti_list = parti_str.split("&&&")
                    print(f"{parti_list[0]} Room, participants:")
                    for i, parti in enumerate(parti_list[1:]):
                        print(i + 1, ".", parti)
                # Received message protocol [NUM 5] from server -> current available rooms
                if msgType == 5:
                    room_len = int(self.client.recv(4).decode())
                    room_str = self.client.recv(room_len).decode()
                    room_list = room_str.split("&&&")
                    self.rooms_list = room_list[:-1]
                    print(f"Current Rooms:")
                    for i, room in enumerate(self.rooms_list):
                        print(i + 1, ".", room)
                # Received message protocol [NUM 6] from server -> participant & room movements:
                if msgType == 6:
                    msgLen = int(self.client.recv(4).decode())
                    msgContent = self.client.recv(msgLen).decode()
                    print("\n" + msgContent)

                # Received message protocol [NUM 7] from server -> if room was removed - True or False:
                if msgType == 7:
                    RoomDelBool = bool(int(self.client.recv(1).decode()))
                    roomNameLen = int(self.client.recv(4).decode())
                    roomName = self.client.recv(roomNameLen).decode()
                    if RoomDelBool:
                        print(f"Successfully removed Room {roomName}!")
                    else:
                        print(f"Failed to Remove Room: {roomName}!")

        except ConnectionResetError:
            print("[ERROR] SORRY SOMETHING WENT WRONG, You where Disconnected !")

    def update_rooms_status(self):
        """
        A methods that generate a room info request from server/
        information needed for client to choose his logging room from an updated info!
        """
        self.client.send("80001m".encode())

    def send(self):
        """
        The send func is a 'threaded' looped method that send messages to the server,
        using a protocol type message and encoding.

        the type messages protocols must be equivalent to the server self.receive() method
        if not the client will be disconnected!

        type message protocols [msgType] from client:
        msgType = 2 -> join a room request"
        msgType = 3 -> exit a room request"
        msgType = 4 -> generate new room request"
        msgType = 5 -> delete a room request"
        msgType = 6 -> broadcast a message request"
        msgType = 7 -> get room participants info request"
        msgType = 8 -> get all rooms status info request"

        NOTICE: threading client connection using send "looped" Client class Methods
                will operate while server 'threaded' self.receive() loop func is operate and online!

        :return: None
        """
        while True:
            while True:  # message length validity:
                msgContent = input()
                if len(msgContent) > MESSAGE_MAX_LEN:
                    print(f"Message cannot exceeds more then {MESSAGE_MAX_LEN} characters!")
                    continue
                break
            msgType = "6"
            if msgContent in ["M", "m"]:
                op = input(
                    "\n1. Join a Room\n2. Generate Room\n3. Delete Room\n4. Room participant Info\n5. Rooms Status \n ")
                if op == "1":
                    self.update_rooms_status()
                    msgType = "2"  # join a room number protocol
                    print("Choose a room:")
                    while True:
                        choice = input()
                        if not choice.isdigit() or 1 > int(choice) or int(choice) > len(self.rooms_list):
                            print("Please choose an option from the list!")
                        else:
                            break
                    msgContent = self.rooms_list[int(choice) - 1]
                if op == "2":
                    msgType = "4"  # generate a room num protocol
                    msgContent = input("Choose a name for your room:")
                if op == "3":
                    msgType = "5"  # delete a room num protocol
                    print("Choose a room to delete:")
                    self.update_rooms_status()
                    while True:
                        choice = input()
                        if not choice.isdigit() or 1 > int(choice) or int(choice) > len(self.rooms_list):
                            print("Please choose an option from the list!")
                        else:
                            break
                    msgContent = self.rooms_list[int(choice) - 1]
                if op == "4":
                    msgType = "7"  # room participant num protocol
                if op == "5":
                    msgType = "8"  # rooms status num protocol
            if msgContent == "exit":
                msgType = "3"  # exit a room num protocol

            msgLen = str(len(msgContent)).zfill(4)
            msg = msgType + msgLen + msgContent
            self.client.send(msg.encode())


client = Client()
client.send_roope_and_thread()