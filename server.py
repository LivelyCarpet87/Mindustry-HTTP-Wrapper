import pexpect
import flask
from flask import render_template, abort, redirect, request, make_response, send_file, g, session, flash
import os

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

# User accounts on the server
accounts = {
    "admin": "PASSWORD_CHANGE_ME_PLEASE",
    "invitee": "CHANGE_THIS_TOO" 
}
secret_key="CHANGEMETOO"
# END CONFIG HERE

if jar_path == "/path/to/server-release.jar":
    print("Open the server.py file to edit the configuration.")
    exit()

child = None
app = flask.Flask(__name__, static_folder='assets')
app.secret_key = secret_key
port = int(os.getenv('PORT', 8090))
logHead=r"\[\d\d\-\d\d\-\d\d\d\d \d\d:\d\d:\d\d\] \[I\]\ "
import time

@app.before_first_request
def init():
    global child
    child = pexpect.spawn(f'{java_path} {memoryLimit} -jar {jar_path}')
    child.sendline(f'config name {serverName}')
    child.sendline(f'config description {desc}')
    child.sendline('config whitelist true')

@app.route('/', methods=['GET'])
def home():
    username = session.get("username")
    if username is None:
        return render_template("login.html")
    return render_template("home.html")

@app.route('/', methods=['POST'])
def login():
    usernameIn = request.form.get('username')
    passwordIn = request.form.get('password')
    if usernameIn in accounts.keys() and accounts[usernameIn] == passwordIn:
        session["username"]=usernameIn
        return render_template("home.html")
    else:
        return render_template("login.html")

def testLoggedIn():
    username = session.get("username")
    if username is None:
        abort(403)

@app.route('/actions/pause-on', methods=['GET'])
def pauseStateOn():
    testLoggedIn()
    child.sendline('pause on')
    return redirect("/")

@app.route('/actions/pause-off', methods=['GET'])
def pauseStateOff():
    testLoggedIn()
    child.sendline('pause off')
    return redirect("/")

@app.route('/actions/save-to-slot/<save_slot>', methods=['GET'])
def saveToSlot(save_slot):
    testLoggedIn()
    if save_slot in ["slot0", "slot1", "slot2"]:
        child.sendline(f'save {save_slot}')
    return redirect("/")

@app.route('/actions/load-slot/<save_slot>', methods=['GET'])
def loadSlot(save_slot):
    testLoggedIn()
    if save_slot in ["slot0", "slot1", "slot2"]:
        child.sendline(f'save {save_slot}')
    return redirect("/")

@app.route('/actions/stop', methods=['GET'])
def stopGame():
    testLoggedIn()
    child.sendline(f'stop')
    return redirect("/")

@app.route('/actions/host', methods=['GET'])
def hostGame():
    testLoggedIn()
    child.sendline(f'host')
    return redirect("/")

@app.route('/actions/letInPlayer', methods=['GET'])
def letInPlayer():
    testLoggedIn()
    child.sendline("config whitelist off")
    return redirect("/")

@app.route('/actions/keepOut', methods=['GET'])
def keepOut():
    testLoggedIn()
    child.sendline("config whitelist on")
    return redirect("/")

@app.route('/actions/tempWhitelistOff', methods=['GET'])
def tempWhitelistOff():
    testLoggedIn()
    child.sendline("config whitelist off")
    time.sleep(60)
    child.sendline("config whitelist on")
    return redirect("/")

@app.route('/debug', methods=['GET'])
def debug():
    return repr(child.after), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)