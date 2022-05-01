import flask
from flask import render_template, abort, redirect, request, make_response, send_file, g, session, flash
import os, socket, subprocess, time, re

# START CONFIG HERE

# Path the the mindustry server jar file
jar_path="/path/to/server-release.jar"

# Path to java
java_path="/usr/bin/java"

# Display name of the server
serverName = "Murder Drones"
# Description for the server
desc="A private server for friends."

# Memory limit when running server. Useful for limited available memory
memoryLimit="-Xmx200M"

# Maximum amount of saved server interactions
maxConvoLen=20

# User accounts on the server
accounts = {
    "admin": {
        "password": "PASSWORD_CHANGE_ME_PLEASE",
        "allowedCommands": ["pause", "host", "stop", "maps", "status"],
        "allowInput": True,
        "seeFullHistory": True,
        },
    "invitee": {
        "password": "PASSWORD_CHANGE_ME_PLEASE",
        "allowedCommands": [],
        "allowInput": False,
        "seeFullHistory": False,
        },
}
secret_key="CHANGEMETOO"
# END CONFIG HERE

if jar_path == "/path/to/server-release.jar":
    print("Open the server.py file to edit the configuration.")
    exit()

mindustrySocket = None
app = flask.Flask(__name__, static_folder='assets')
app.secret_key = secret_key
port = int(os.getenv('PORT', 8090))
logHead=r"\[\d\d\-\d\d\-\d\d\d\d \d\d:\d\d:\d\d\] \[I\]\ "
conversation=[]
conversationPointer=-1
maps=[]

def inputCommand(command, byUser=True):
    global conversationPointer
    mindustrySocket.sendall(command.encode()+b'\n')
    if byUser:
        conversationPointer += 1
    return getOutput()

def getOutput():
    global conversation, conversationPointer
    newExchange = b""
    while True:
        try:
            newExchange += mindustrySocket.recv(1)
        except TimeoutError:
            break
    newExchange = re.sub(r'\x1b\[\d+m','',newExchange.decode())
    newExchange = newExchange
    if newExchange != "":
        conversationPointer -= 1
        if len(conversation) <= maxConvoLen:
            conversation.append(newExchange)
        else:
            conversation.pop(0)
            conversation.append(newExchange)
    else:
        conversationPointer -= 1
        if len(conversation) <= maxConvoLen:
            conversation.append("Server timed out")
        else:
            conversation.pop(0)
            conversation.append("Server timed out")
    return newExchange




@app.before_first_request
def init():
    global mindustrySocket, maps
    child = subprocess.Popen([java_path, memoryLimit, "-jar", jar_path], stdin=subprocess.PIPE, 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    child.stdin.write(f'config name {serverName}\n'.encode())
    child.stdin.write(f'config description {desc}\n'.encode())
    child.stdin.write(b'config whitelist true\n')
    child.stdin.write(b'config socketInput true\n')
    time.sleep(1)
    mindustrySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mindustrySocket.connect( ("localhost", 6859) )
    mindustrySocket.settimeout(5.0)

    mapsCommandOutput = inputCommand("maps")
    matches = re.findall(r"([A-Za-z_]*):\ [DefaultCustom]* \/ \d+x\d+", mapsCommandOutput)
    for match in matches:
        maps.append(match)

@app.route('/', methods=['GET'])
def home():
    username = session.get("username")
    if username is None:
        return render_template("login.html")
    return render_template("home.html", maps=maps, conversation = conversation, conversationPointer=conversationPointer)

@app.route('/', methods=['POST'])
def login():
    usernameIn = request.form.get('username')
    passwordIn = request.form.get('password')
    if usernameIn in accounts.keys() and accounts[usernameIn]["password"] == passwordIn:
        session["username"]=usernameIn
        return render_template("home.html")
    else:
        return render_template("login.html")

def testLoggedIn():
    username = session.get("username")
    if username is None:
        abort(403)

def testCanRun(command):
    username = session.get("username")
    if username is None:
        abort(403)
    if command not in accounts[username]["allowedCommands"]:
        abort(403)

@app.route('/actions/pause-on', methods=['GET'])
def pauseStateOn():
    testLoggedIn()
    inputCommand('pause on')
    return redirect("/")

@app.route('/actions/pause-off', methods=['GET'])
def pauseStateOff():
    testLoggedIn()
    inputCommand('pause off')
    return redirect("/")

@app.route('/actions/save-to-slot/<save_slot>', methods=['GET'])
def saveToSlot(save_slot):
    testLoggedIn()
    if save_slot in ["slot0", "slot1", "slot2"]:
        inputCommand(f'save {save_slot}')
    return redirect("/")

@app.route('/actions/load-slot/<save_slot>', methods=['GET'])
def loadSlot(save_slot):
    testLoggedIn()
    if save_slot in ["slot0", "slot1", "slot2"]:
        inputCommand(f'load {save_slot}')
    return redirect("/")

@app.route('/actions/stop', methods=['GET'])
def stopGame():
    testLoggedIn()
    inputCommand(f'stop')
    return redirect("/")

@app.route('/actions/host', methods=['GET'])
def hostGame():
    testLoggedIn()
    inputCommand(f'host')
    return redirect("/")

@app.route('/actions/host', methods=['POST'])
def hostGameDefined():
    testLoggedIn()
    map=request.form.get('map')
    mode=request.form.get('mode')
    if map not in ["Ancient_Caldera", "Archipelago", "Debris_Field", "Fork", "Fortress", "Glacier", "Islands", "Labyrinth", "Maze",
    "Molten_Lake", "Mud_Flats", "Shattered", "Tendrils", "Triad", "Veins", "Wasteland"]:
        abort(400)
    if mode not in ["sandbox", "survival", "attack", "pvp"]:
        abort(400)
    inputCommand(f'host {map} {mode}')
    return redirect("/")

@app.route('/actions/runwave', methods=['GET'])
def runwave():
    testLoggedIn()
    inputCommand(f'runwave')
    return redirect("/")

@app.route('/actions/disableWhitelist', methods=['GET'])
def letInPlayer():
    testLoggedIn()
    inputCommand("config whitelist off")
    return redirect("/")

@app.route('/actions/enableWhitelist', methods=['GET'])
def keepOut():
    testLoggedIn()
    inputCommand("config whitelist on")
    return redirect("/")

@app.route('/actions/whitelistRecentPlayer', methods=['GET'])
def tempWhitelistOff():
    testLoggedIn()
    global conversationPointer
    recentActivity = getOutput()
    matches = re.findall(r"([A-Za-z=\d]{24})", recentActivity)
    if len(matches) >= 1:
        inputCommand(f"whitelist-add {matches[-1]}")
    else:
        conversation.append("No players joining recently")
    return redirect("/")

@app.route('/status', methods=['GET'])
def debug():
    inputCommand("status")
    return redirect("/")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)