from flask import Flask, request
from flask_cors import CORS
import pyautogui as pag, io, base64, http.server, socketserver, threading, socket, os
from tkinter import *
from PIL import Image

# html stránka
http_port = 56789   
directory = '.'  # This will serve files from the current directory
handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(("", http_port), handler)

# povolenie pyautogui pohybovanie sa v rohoch obrazovky
pag.FAILSAFE = False

# flask aplikacia
app = Flask(__name__)

# CORS sprostosť
CORS(app)

start_x, start_y = None, None
occupiedBy = None

# heslo
password = ""

root = Tk()

root.title("Easy Remote")
root.iconbitmap("assets/easy-remote.ico")
root.geometry("340x100")

tk_row1 = 10
tk_row2 = 50
tk_row3 = 90
tk_row4 = 130

def startFlaskServer():
    app.run(host="0.0.0.0", port=5000)

def clearScreen():

    for i in root.winfo_children():
        i.destroy()

def tkScreen1():

    global entry_pass

    clearScreen()

    label_passinput = Label(root, text="Create password:")
    label_passinput.place(x=20, y=tk_row1)

    entry_pass = Entry(root, show="•")
    entry_pass.place(x=150, y=tk_row1+3)

    button_start = Button(root, text="Start", width=7, command=start)
    button_start.place(x=248, y=tk_row2)

    root.mainloop()

def tkScreen2():

    clearScreen()

    label_starting = Label(root, text="Starting server...")
    label_starting.place(x=105, y=tk_row1)

def tkScreen3():

    clearScreen()

    global entry_serverpass, label_stopserverinfo

    root.geometry("340x210")

    label_serverurl = Label(root, text="URL:")
    label_serverurl.place(x=20, y=tk_row1)

    entry_serverurl = Entry(root)
    entry_serverurl.insert(0, f"{socket.gethostbyname(socket.gethostname())}:{http_port}")
    entry_serverurl.config(state="readonly")
    entry_serverurl.place(x=60, y=tk_row1+2)

    label_serverpass = Label(root, text="Password:")
    label_serverpass.place(x=20, y=tk_row2)

    entry_serverpass = Entry(root, show="•")
    entry_serverpass.insert(0, password)
    entry_serverpass.config(state="readonly")
    entry_serverpass.place(x=95, y=tk_row2+2)

    button_showpass = Button(root, text="👁")
    button_showpass.place(x=260, y=tk_row2-2)
    button_showpass.bind("<ButtonPress>", showPassword)
    button_showpass.bind("<ButtonRelease>", hidePassword)

    label_stopserverinfo = Label(root, text="To connect to this computer, type the URL \nabove into a web browser on a phone. \nClose this app to stop. If the app takes too \nlong to close, try refreshing the client's web \nbrowser.", justify=LEFT)
    label_stopserverinfo.place(x=20, y=tk_row3)

    root.protocol("WM_DELETE_WINDOW", onClose)

def showPassword(event):

    entry_serverpass.config(show="")

def hidePassword(event):

    entry_serverpass.config(show="•")

def startSite():

    # logika pre POST requesty

    @app.route("/", methods=["POST"])
    def post():
        global start_x, start_y, occupiedBy

        data = request.get_json()

        if occupiedBy == request.remote_addr:
            if data["type"] == "browserRefresh":
                if request.remote_addr == occupiedBy:
                    occupiedBy = None
                    return "refresh true"
                
                else:
                    return "refresh false"
                
            if data["type"] == "mousepadTouch":
                start_x, start_y = pag.position()
                return "empty"
            
            if data["type"] == "mousepadMove":
                if start_x and start_y:
                    offset_x, offset_y = data["data"].split("/")
                    new_x = start_x + float(offset_x)
                    new_y = start_y + float(offset_y)
                    pag.moveTo(new_x, new_y)
                return "empty"
            
            if data["type"] == "mousepadRelease":
                end_x, end_y = pag.position()
                if end_x == start_x and end_y == start_y:
                    pag.click()
                return "empty" 
        
            if data["type"] == "hotkeyPress":
                if data["data"] == "Backspace":
                    pag.press("backspace")
                elif data["data"] == "Enter":
                    pag.press("enter")
                elif data["data"] == "Esc":
                    pag.press("esc")
                elif data["data"] == "Caps Lock":
                    pag.press("capslock")
                return "empty"
            
            if data["type"] == "textWrite":
                pag.write(data["data"])
                return "empty"
            
            if data["type"] == "showScreen":
                screenshot = pag.screenshot()

                cursor_x, cursor_y = pag.position()
                cursor_image = Image.open("assets/cursor_mod.png")
                screenshot.paste(cursor_image, (cursor_x, cursor_y), cursor_image)
                
                screenshot_bytes = io.BytesIO()
                screenshot.thumbnail((800, 800))
                screenshot.save(screenshot_bytes, format="PNG")
                screenshot_base64 = base64.b64encode(screenshot_bytes.getvalue()).decode('utf-8')
                return screenshot_base64

            if data["type"] == "inactive dc" or data["type"] == "dc":
                occupiedBy = None
                return "empty"
            
        elif not occupiedBy:

            if data["type"] == "connect":
                if data["data"] == password:
                    occupiedBy = request.remote_addr
                    return "connect success"
                
                else:
                    return "connect failed"
                
            else:
                return "unverified"
            
        else:
            return "occupied"

    # zakázanie GET requestov            
    @app.route("/", methods=["GET"])
    def get():
        return "'GET' requests not allowed"
    
    global http_thread, flask_thread

    # hostovanie stránky
    http_thread = threading.Thread(target=httpd.serve_forever)
    http_thread.start()

    # hostovanie flasku
    flask_thread = threading.Thread(target=startFlaskServer)
    flask_thread.start()
    
    tkScreen3()

def onClose():
    
    httpd.shutdown()
    root.destroy()
    os._exit(0)

def start():

    global password, startSite_thread

    password = entry_pass.get().strip()

    startSite_thread = threading.Thread(target=startSite)
    startSite_thread.start()

    tkScreen2()

if __name__ == "__main__":
    tkScreen1()