from ttkbootstrap import *
from ttkbootstrap.constants import *
from functools import partial
import serial.tools.list_ports, time, serial, threading, json, os, winshell, pystray, socket, http.server, socketserver, pyperclip, io, base64, sys
import pyautogui as pag

pag.FAILSAFE = False

# TODO: remove this ip
CORSOrigins = ["http://127.0.0.1:5500"]
initialX, initialY = None, None
screenshareQuality = 800

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):

    def end_headers(self):
        origin = self.headers.get("Origin")
        if origin in CORSOrigins:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

    def do_POST(self):

        global screenshareQuality
        
        content_length = int(self.headers['Content-Length'])  
        post_data = self.rfile.read(content_length)  

        response = None     

        data = json.loads(post_data.decode('utf-8'))

        print(data)
        
        if data["type"] == "addToCORS":
            CORSOrigins.append(data["data"])
            self.send_response(200, "OK")
            self.end_headers()
        
        elif data["type"] == "delFromCORS":
            try:
                CORSOrigins.remove(data["data"])
                self.send_response(200, "OK")
                self.end_headers()

            except ValueError:
                self.send_response(404, "Not Found")
                self.end_headers()

        elif data["type"] == "stateCheck":
            self.send_response(200, "OK")
            self.end_headers()

        elif data["type"] == "screen":

            self.send_response(204, "No Content")
            self.end_headers()

        elif data["type"] == "keyPress":
            pyperclip.copy(data["data"])
            pag.hotkey("ctrl", "v")

            self.send_response(204, "No Content")
            self.end_headers()

        elif data["type"] == "hotkeyPress":
            pag.hotkey(data["data"])

            self.send_response(204, "No Content")
            self.end_headers()

        elif data["type"] == "mouseDown":

            global initialX, initialY

            initialX, initialY = pag.position()

            self.send_response(204, "No Content")
            self.end_headers()

        elif data["type"] == "mouseMove":

            relativeX, relativeY = data["data"].split()
            relativeX, relativeY = int(float(relativeX)), int(float(relativeY))

            pag.moveTo(initialX + relativeX, initialY + relativeY)
            print("moving")

            self.send_response(204, "No Content")
            self.end_headers()

        elif data["type"] == "mouseUp":

            currentX, currentY = pag.position()
            if currentX == initialX and currentY == initialY:
                pag.click()

            self.send_response(204, "No Content")
            self.end_headers()

        elif data["type"] == "screenshare":

            screenshot = pag.screenshot()

            cursor_x, cursor_y = pag.position()
            cursor_image = Image.open("assets/cursor_mod.png")
            screenshot.paste(cursor_image, (cursor_x, cursor_y), cursor_image)
            
            screenshot_bytes = io.BytesIO()
            screenshot.thumbnail((screenshareQuality, screenshareQuality))
            screenshot.save(screenshot_bytes, format="PNG")
            response = base64.b64encode(screenshot_bytes.getvalue()).decode('utf-8')

            self.send_response(200, "OK")
            self.end_headers()

        elif data["type"] == "screenshareQuality":

            if data["data"] == "high":
                screenshareQuality = 1200
            elif data["data"] == "medium":
                screenshareQuality = 800
            elif data["data"] == "low":
                screenshareQuality = 400

            self.send_response(204, "No Content")
            self.end_headers()

        if not response:
            response = {}

        self.wfile.write(str(response).replace("'", '"').encode('utf-8'))  




class App:

    def __init__(self):

        self.instanceLock = self.checkSingleInstance()
        if not self.instanceLock:
            os._exit(1)
        threading.Thread(target=self.checkSecondInstance, args=(self.instanceLock,), daemon=True).start()

        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = 400, 400
        self.POPUP_WIDTH, self.POPUP_HEIGHT = 300, 200

        self.FONT_TITLE = ("Helvetica", 15, "bold")
        self.FONT_DEFAULT = ("Helvetica", 10)

        self.app = Window(themename="darkly")    # Tkinter instance
        self.app.title("Simple Remote Admin Panel")
        self.app.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.app.resizable(False, False)
        self.app.protocol("WM_DELETE_WINDOW", self.onClose)

        with open("config.json", "r", encoding="utf-8") as f:
            self.settings = json.loads(f.read())

        self.restoredSettings = '{"onNextStartup": "setup", "showNoticeOnClose": "1", "state": "1", "controllerIp": "0"}'

        self.opened = True 
        self.controllerSerialConn = None
        self.thread = None
        self.threadEnd = False
        self.canThrowErrorScreen = False
        self.thePort = None
        self.factoryReset = False

        self.trayIconImage = Image.open("assets/logo.png")  
        self.trayIconMenu = pystray.Menu()
        self.trayIcon = pystray.Icon("SimpleRemote", self.trayIconImage, "Simple Remote", self.trayIconMenu)
        threading.Thread(target=self.trayIcon.run, daemon=True).start()

        self.serverPort = 65432
        self.server = socketserver.TCPServer(("", self.serverPort), CORSRequestHandler)
        self.serverThread = None
        
    def checkSingleInstance(self, port=65433):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.listen()
            return sock
        except:
            sock.connect(("127.0.0.1", port))
            sock.sendall(b"INSTANCE_DETECTED")
            sock.close()
            return False

    def checkSecondInstance(self, lock):
        
        while True:
            try:
                conn, _ = lock.accept()
                message = conn.recv(1024).decode("utf-8")
                if message == "INSTANCE_DETECTED":
                    self.showWindow()
                conn.close()
            except:
                None

    def saveSettings(self):

        with open("config.json", "w", encoding="utf-8") as f:
            if self.factoryReset:
                f.write(self.restoredSettings)
            else:
                f.write(json.dumps(self.settings))


    def setupClose(self, popup):
        """Closing the window while running setup."""

        popup.destroy()

        self.sendCommandToController("END setup")
        
        os._exit(0)

    def runClose_dontShowAgain(self, popup):
        """Closing the window while normally using."""

        self.settings["showNoticeOnClose"] = "0"
        popup.destroy()

        self.runClose()
        
    def runClose(self, popup = None):
        """Closing the window while normally using."""
        if popup:
            popup.destroy()
        if self.app:
            self.app.withdraw()
        self.opened = False

    def quitApp(self):
        """Quit the app."""

        self.sendCommandToController("END setup")

        self.instanceLock.close()
        if self. serverThread and self.serverThread.is_alive():
            self.stateOff()

        self.saveSettings()

        os._exit(0)

    def onClose(self):
        
        if self.settings["onNextStartup"] == "setup":
            popup = Toplevel("Are you sure?")
            popup.geometry(f"{self.POPUP_WIDTH}x{self.POPUP_HEIGHT}")

            Label(popup, text="Are you sure you want to exit and interrupt the setup?", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.POPUP_WIDTH-20).pack(pady=10)

            controls = Frame(popup, width=self.WINDOW_WIDTH, height=30)
            controls.pack_propagate(False)
            controls.pack(side="bottom", fill="x", padx=10, pady=10)
            noBtn = Button(controls, text="No", bootstyle="primary", width=10, cursor="hand2", command=popup.destroy)
            noBtn.pack(side="left")
            yesBtn = Button(controls, text="Yes", bootstyle="primary", width=10, cursor="hand2", command=partial(self.setupClose, popup))
            yesBtn.pack(side="right")
            
            popup.transient()
            popup.grab_set()
            self.app.wait_window(popup)
        
        elif self.settings["onNextStartup"] == "run" and self.settings["showNoticeOnClose"] == "1":
            popup = Toplevel("Notice")
            popup.geometry(f"{self.POPUP_WIDTH}x{self.POPUP_HEIGHT}")

            Label(popup, text="Simple Remote will continue to run in the background. To fully quit, click the \"Quit\" button in the Admin Panel or in the Icon Tray.", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.POPUP_WIDTH-20).pack(pady=10)

            controls = Frame(popup, width=self.WINDOW_WIDTH, height=30)
            controls.pack_propagate(False)
            controls.pack(side="bottom", fill="x", padx=10, pady=10)
            Button(controls, text="OK, don't show again.", bootstyle="primary", cursor="hand2", command=partial(self.runClose_dontShowAgain, popup)).pack(side="left")
            Button(controls, text="OK.", bootstyle="primary", width=10, cursor="hand2", command=partial(self.runClose, popup)).pack(side="right")

            popup.transient()
            popup.grab_set()
            self.app.wait_window(popup)

        else:
            self.runClose()

    

    def showWindow(self):
        threading.Thread(target=self.createWindow, daemon=True).start()
        

    def createWindow(self):
        if self.opened:
            self.app.wm_deiconify()
            return
        
        self.opened = True

        self.app.wm_deiconify()

        self.mainScreen1()


    def checkForTracebackInResponse(self, response):

        print(0)
        try:
            if response.split()[0] == "Traceback":
                print(1)
                print(self.controllerSerialConn.readall().decode().strip())
        except:
            None

    def getResponseFromController(self):

        """
        Use to get the response from the controller.
        This should be used only with "sendCommandToController" function.
        """

        try:
            response = self.controllerSerialConn.readline().decode().strip()
            self.checkForTracebackInResponse(response)
            return response
        except:
            return False

    def sendCommandToController(self, command):
        
        """
        Use to send a command to the controller.
        This should be used when you won't get immediate response from the controller in combination
        with "getResponseFromController" function.
        """

        try:
            self.controllerSerialConn.write((command+'\n').encode())
        except:
            return False

    def IOtoController(self, command):

        """
        Use to send a command to the controller and get a response from it.
        This should be used when an immediate response from controller is expected.
        """

        try:
            print("Command:", command)

            self.controllerSerialConn.write((command+'\n').encode())
            response = self.controllerSerialConn.readline().decode().strip()
            self.checkForTracebackInResponse(response)
        
            print("Response:", response, "\n---")

            return response
        except:
            return False

        

    def controllerCheckThread(self):

        global screen2Controls, screen2State, screen2NextBtn

        print("Thread started")

        while not self.threadEnd:

            if not self.thePort:
                comPorts = self.listComPorts()

                for port in comPorts:
                    try:
                        self.controllerSerialConn = serial.Serial(port, baudrate=115200, timeout=1)
                        response = self.IOtoController("ADMIN_PANEL_CONNECT")
                        if response == "SIMPLE_REMOTE_CONNECT":
                            self.thePort = port
                            break
                        else:
                            self.controllerSerialConn.close()

                    except serial.serialutil.SerialException as e:
                        print(e)
                        None

                    except e:
                        print(e)
                        self.controllerSerialConn.close()
                    
                

            else:

                if self.thePort not in self.listComPorts():

                    self.controllerSerialConn.close()
                    self.thePort = None
                    try:
                        screen2State.config(text="Controller not found", bootstyle="danger")
                        screen2NextBtn.config(state="disabled")

                    except tk.TclError:
                        None   

                    if self.canThrowErrorScreen:
                        self.canThrowErrorScreen = False
                        self.setupScreenError() 

                else:
                    try:
                        screen2State.config(text="Controller found", bootstyle="success")
                        screen2NextBtn.config(state="enabled")
                    except tk.TclError:
                        None
                        
            time.sleep(0.5)

    def listComPorts(self):

        ports = serial.tools.list_ports.comports()
        
        connected_ports = []
        for port in ports:
            connected_ports.append(port.name)

        return connected_ports


    def clearScreen(self):

        global screen2Controls, screen2State, screen2NextBtn

        for i in self.app.winfo_children():
            i.destroy()


        screen2Controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        screen2Controls.pack_propagate(False)
        screen2State = Label(self.app, text="Controller not found", font=self.FONT_DEFAULT, bootstyle="danger")
        screen2NextBtn = Button(screen2Controls, text="Next", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen3, state="disabled")


    def setupScreen1(self):

        self.threadEnd = False
        self.thread = threading.Thread(target=self.controllerCheckThread, daemon=True)
        self.thread.start()

        self.clearScreen()

        Label(self.app, text="Setup", font=self.FONT_TITLE).pack(pady=10)
        Label(self.app, text="Welcome to setup. Click Next to start.", font=self.FONT_DEFAULT).pack()

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        
        if self.settings["onNextStartup"] == "setup":
            Button(controls, text="Exit", bootstyle="primary", width=10, cursor="hand2", command=self.app.quit).pack(side="left")
        elif self.settings["onNextStartup"] == "run":
            Button(controls, text="Back", bootstyle="primary", width=10, cursor="hand2", command=self.mainScreen1).pack(side="left")

        Button(controls, text="Next", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen2).pack(side="right")


    def setupScreen2(self):

        self.clearScreen()

        self.canThrowErrorScreen = False

        Label(self.app, text="Connect the controller to this computer with a USB cable. It will be automatically detected.", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.WINDOW_WIDTH-20).pack(padx=10, pady=10)
        screen2State.pack(padx=10, pady=10)

        screen2Controls.pack(side="bottom", fill="x", padx=10, pady=10)
        Button(screen2Controls, text="Back", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen1).pack(side="left")
        screen2NextBtn.pack(side="right")


    def setupScreenError(self):

        self.clearScreen()

        Label(self.app, text="Connection error", font=self.FONT_TITLE).pack(pady=10)
        Label(self.app, text="Controller disconnected. Please connect it back and try again.", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.WINDOW_WIDTH-20).pack(padx=10, pady=10)

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        Button(controls, text="Back", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen2).pack(side="left")


    def setupScreen3_OnInput(self, wifiNameEntry, nextBtn, _):
        
        if wifiNameEntry.get().strip():
            nextBtn.config(state="enabled", cursor="hand2")
        else:
            nextBtn.config(state="disabled", cursor="arrow")


    def waitForWifiTest(self, wifiNameDropdown, wifiPassEntry, wifiListRefreshBtn, wifiTestResult, backBtn, nextBtn):
        
        while True:
            response = self.getResponseFromController()
            if response:
                break

        if response[0] == "1":
            backBtn.config(state="enabled", cursor="hand2")
            nextBtn.config(state="enabled", text="Next", cursor="hand2", command=self.setupScreen4)
            wifiTestResult.config(bootstyle="success", text="Connected")

            response = response.split()
            self.settings["controllerIp"] = response[1]

        else:
            backBtn.config(state="enabled", cursor="hand2")
            nextBtn.config(state="enabled", text="Test", cursor="hand2")
            wifiPassEntry.config(state="enabled", cursor="xterm")
            wifiNameDropdown.config(state="enabled")
            wifiListRefreshBtn.config(state="enabled", cursor="hand2")
            wifiTestResult.config(bootstyle="danger", text="Failed")

    
    def getWifiList(self):

        response = self.IOtoController("WIFI_LIST")

        while not response:
            response = self.getResponseFromController()

        response = json.loads(response)
        filter = []
        wifiListFiltered = []

        for wifi in response:
            if wifi[0] not in filter and wifi[0] != "":
                filter.append(wifi[0])
                wifiListFiltered.append(wifi)
        wifiListFiltered.sort()

        return wifiListFiltered



    def setupScreen3_WifiTest(self, wifiNameDropdown, wifiNameSelectedOption, wifiPassEntry, wifiListRefreshBtn, wifiTestResult, backBtn, nextBtn):

        backBtn.config(state="disabled", cursor="arrow")
        nextBtn.config(state="disabled", cursor="arrow")
        wifiPassEntry.config(state="disabled", cursor="arrow")
        wifiNameDropdown.config(state="disabled")
        wifiListRefreshBtn.config(state="disabled", cursor="arrow")
        wifiTestResult.config(bootstyle="info", text="Testing...")

        command = [wifiNameSelectedOption.get(), wifiPassEntry.get()]
        self.sendCommandToController("WIFI_TEST " + json.dumps(command))
        print("WIFI_TEST " + json.dumps(command))
        
        thread = threading.Thread(target=partial(self.waitForWifiTest, wifiNameDropdown, wifiPassEntry, wifiListRefreshBtn, wifiTestResult, backBtn, nextBtn), daemon=True)
        thread.start()


    def setupScreen3_OnWifiSelect(self, wifiPassEntry, wifiPassLabel, nextBtn, wifiList, selectedWifiName):
        
        wifiPassEntry.delete(0, END)

        for wifi in wifiList:
            if wifi[0] == selectedWifiName:
                if wifi[1] == 0:
                    wifiPassLabel.config(foreground="grey")
                    wifiPassEntry.config(state="disabled")
                    nextBtn.config(state="enabled")
                else:
                    wifiPassLabel.config(foreground="white")
                    wifiPassEntry.config(state="enabled")
                    nextBtn.config(state="disabled")


    def setupScreen3(self):

        self.canThrowErrorScreen = True

        wifiList = self.getWifiList()
        wifiNames = []
        for wifi in wifiList:
            wifiNames.append(wifi[0])
        wifiNames.insert(0, " ")
        
        self.clearScreen() 

        Label(self.app, text="Select the network that this computer is connected to and enter it's password. The controller will be connecting to this network. Make sure the controller is in range of the WiFi. (If you get 'failed' error, try bringing the controller closer to your router and try again.)", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.WINDOW_WIDTH-20).pack(padx=10, pady=10)

        wifiNameFrame = Frame(self.app)
        wifiNameFrame.pack()
        Label(wifiNameFrame, text="WiFi:", font=self.FONT_DEFAULT).pack(side=LEFT, padx=5)

        wifiPassFrame = Frame(self.app)
        wifiPassFrame.pack()
        wifiPassLabel = Label(wifiPassFrame, text="Password:", font=self.FONT_DEFAULT)
        wifiPassLabel.pack(side=LEFT, padx=5)
        wifiPassEntry = Entry(wifiPassFrame, width=10, show="•")
        wifiPassEntry.pack(padx=5)

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        backBtn = Button(controls, text="Back", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen2)
        backBtn.pack(side="left")
        nextBtn = Button(controls, text="Test", bootstyle="primary", width=10, cursor="hand2", state="disabled")
        nextBtn.pack(side="right")

        wifiNameSelectedOption = tk.StringVar()
        wifiNameSelectedOption.set(" ")
        wifiNameDropdown = OptionMenu(wifiNameFrame, wifiNameSelectedOption, *wifiNames, command=partial(self.setupScreen3_OnWifiSelect, wifiPassEntry, wifiPassLabel, nextBtn, wifiList))
        wifiNameDropdown.pack(padx=5)

        wifiPassEntry.bind("<KeyRelease>", partial(self.setupScreen3_OnInput, wifiPassEntry, nextBtn))

        wifiListRefreshBtn = Button(self.app, text="Refresh", cursor="hand2", command=self.setupScreen3)
        wifiListRefreshBtn.pack()

        wifiTestResult = Label(self.app, text="", font=self.FONT_DEFAULT)
        wifiTestResult.pack(padx=10, pady=10)

        nextBtn.config(command=partial(self.setupScreen3_WifiTest, wifiNameDropdown, wifiNameSelectedOption, wifiPassEntry, wifiListRefreshBtn, wifiTestResult, backBtn, nextBtn))

    def setupScreen4_onNext(self, passwordEntry):

        self.sendCommandToController("ACCESS_PASSWORD " + passwordEntry.get().strip())
        self.setupScreen5()
        
    def setupScreen4_onInput(self, passwordEntry, nextBtn, _):

        if passwordEntry.get().strip():
            nextBtn.config(state="enabled", cursor="hand2")
        else:
            nextBtn.config(state="disabled", cursor="arrow")

    def setupScreen4(self):

        self.clearScreen() 

        Label(self.app, text="Enter a password that will be used for authenification into Simple Remote.", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.WINDOW_WIDTH-20).pack(padx=10, pady=10)

        passwordEntry = Entry(self.app, width=10, show="•")
        passwordEntry.pack(pady=5)

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        backBtn = Button(controls, text="Back", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen3)
        backBtn.pack(side="left")
        nextBtn = Button(controls, text="Next", bootstyle="primary", width=10, cursor="hand2", state="disabled", command=partial(self.setupScreen4_onNext, passwordEntry))
        nextBtn.pack(side="right")

        passwordEntry.bind("<KeyRelease>", partial(self.setupScreen4_onInput, passwordEntry, nextBtn))

    def setupScreen5(self):

        self.clearScreen()

        Label(self.app, text="You can unplug the controller from this device, plug it into your motherboard on F_PANEL connector and into a power adapter. Next steps won't require the controller.", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.WINDOW_WIDTH-20).pack(padx=10, pady=10)

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        backBtn = Button(controls, text="Back", bootstyle="primary", width=10, cursor="hand2", state="disabled")
        backBtn.pack(side="left")
        nextBtn = Button(controls, text="Next", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen6)
        nextBtn.pack(side="right")

        # TODO: Send "END" command to the controller and tell it to change it's onNextStartup to "run"
        self.sendCommandToController("PC_IP " + socket.gethostbyname(socket.gethostname()))
        self.sendCommandToController("END run")
        self.threadEnd = True


    def setupScreen6(self):

        self.clearScreen()

        Label(self.app, text="Your next step should be setting a static IP address for your controller in your router. This program has the controller's IP saved in it's settings. This step avoids possible need to constantly change the saved IP in the settings, however, it's not mandatory.", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.WINDOW_WIDTH-20).pack(padx=10, pady=10)

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        backBtn = Button(controls, text="Back", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen5)
        backBtn.pack(side="left")
        nextBtn = Button(controls, text="Next", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen7)
        nextBtn.pack(side="right")


    def setupScreen7_addToStartup(self, addToStartupBtn):

        username = os.environ.get("USERNAME")
        startupPath = f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        target_file = sys.executable

        with winshell.shortcut(startupPath + "\\SimpleRemote.lnk") as shortcut:
            shortcut.path = target_file
            shortcut.description = "Simple Remote"

        addToStartupBtn.config(state="disabled", cursor="arrow")

        Label(self.app, text="Success", bootstyle="success", font=self.FONT_DEFAULT).pack(pady=10)
        Label(self.app, text="You can toggle the startup in windows settings.", font=self.FONT_DEFAULT).pack()
        Button(self.app, text="Open Settings", bootstyle="primary", cursor="hand2", command=partial(os.system, "start ms-settings:startupapps")).pack(pady=10)


    def setupScreen7(self):

        self.clearScreen()

        Label(self.app, text="Please add Simple Remote to your Startup Apps. This way, Simple Remote is always ready to use.", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.WINDOW_WIDTH-20).pack(padx=10, pady=10)

        addToStartupBtn = Button(self.app, text="Add to Startup Apps", cursor="hand2")
        addToStartupBtn.pack(pady=10)

        addToStartupBtn.config(command=partial(self.setupScreen7_addToStartup, addToStartupBtn))

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        backBtn = Button(controls, text="Back", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen6)
        backBtn.pack(side="left")
        nextBtn = Button(controls, text="Finish", bootstyle="primary", width=10, cursor="hand2", command=self.setupScreen8)
        nextBtn.pack(side="right")

    
    def setupScreen8(self):

        self.clearScreen()
        
        Label(self.app, text="Setup Finished!", font=self.FONT_TITLE).pack(pady=10)

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        backBtn = Button(controls, text="Back", bootstyle="primary", width=10, state="disabled")
        backBtn.pack(side="left")
        nextBtn = Button(controls, text="Finish", bootstyle="primary", width=10, cursor="hand2", command=self.mainScreen1)
        nextBtn.pack(side="right")

    
    def stateOn(self):
        if self.serverThread and self.serverThread.is_alive():
            print("Server already running. Restarting...")
            self.stateOff()
        print("Turning on...")
        if self.settings["controllerIp"] not in CORSOrigins:
            CORSOrigins.append(self.settings["controllerIp"])
        self.serverThread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.serverThread.start()
        print(f"Listening on IP {socket.gethostbyname(socket.gethostname())} on port {self.serverPort}")


    def stateOff(self):
        print("Shutting down...")
        self.server.shutdown()
        print("Server shut down.")


    def toggleState(self, stateLabel, *args):

        if self.settings["state"] == "0":
            self.settings["state"] = "1"

            self.stateOn()

            stateLabel.config(text="ON", bootstyle="success")

            self.trayIcon.menu = pystray.Menu(
                pystray.MenuItem("Open", self.showWindow, default=True),  
                pystray.MenuItem("Toggle state: ON", partial(self.toggleState, stateLabel)),
                pystray.MenuItem("Quit", self.quitApp)
            )
            self.trayIcon.update_menu()

        else:
            self.settings["state"] = "0"

            self.stateOff()

            stateLabel.config(text="OFF", bootstyle="danger")

            self.trayIcon.menu = pystray.Menu(
                pystray.MenuItem("Open", self.showWindow, default=True),  
                pystray.MenuItem("Toggle state: OFF", partial(self.toggleState, stateLabel)),
                pystray.MenuItem("Quit", self.quitApp)
            )
            self.trayIcon.update_menu()



    def mainScreen1(self):

        self.saveSettings()
        self.clearScreen()

        self.settings["onNextStartup"] = "run"

        if not self.threadEnd:
            self.threadEnd = True

        Label(self.app, text="Simple Remote", font=self.FONT_TITLE).pack(pady=(10, 5))
        Label(self.app, text="Admin Panel", font=self.FONT_DEFAULT).pack()

        Label(self.app, text=f'Controller IP: {self.settings["controllerIp"]}', font=self.FONT_DEFAULT).pack(pady=(5, 0))

        stateFrame = Frame(self.app)
        stateFrame.pack(pady=(20, 5))
        Label(stateFrame, text="Current state: ", font=self.FONT_DEFAULT).pack(side=LEFT)
        if self.settings["state"] == "1":
            self.stateOn()
            stateLabel = Label(stateFrame, text="ON", bootstyle="success")
            self.trayIcon.menu = pystray.Menu(
                pystray.MenuItem("Open", self.showWindow, default=True),  
                pystray.MenuItem("Toggle state: ON", partial(self.toggleState, stateLabel)),
                pystray.MenuItem("Quit", self.quitApp)
            )
        else:
            stateLabel = Label(stateFrame, text="OFF", bootstyle="danger")
            self.trayIcon.menu = pystray.Menu(
                pystray.MenuItem("Open", self.showWindow, default=True),  
                pystray.MenuItem("Toggle state: OFF", partial(self.toggleState, stateLabel)),
                pystray.MenuItem("Quit", self.quitApp)
            )

        self.trayIcon.update_menu()

        stateLabel.pack()
        Button(self.app, text="Toggle", bootstyle="primary", cursor="hand2", command=partial(self.toggleState, stateLabel)).pack(pady=5)
        
        Label(self.app, text="Additional tools", font=self.FONT_DEFAULT).pack(pady=(20, 5))

        additionalToolsRow1Frame = Frame(self.app)
        additionalToolsRow1Frame.pack(pady=(10, 5))
        Button(additionalToolsRow1Frame, text="Settings", bootstyle="primary", cursor="hand2", command=self.settingsScreen1).grid(row=0, column=0, padx=5)
        Button(additionalToolsRow1Frame, text="Controller Setup", bootstyle="primary", cursor="hand2", command=self.setupScreen1).grid(row=0, column=1, padx=5)
        Button(additionalToolsRow1Frame, text="Factory Reset", bootstyle="primary", cursor="hand2", command=self.factoryResetPopup).grid(row=0, column=2, padx=5)

        additionalToolsRow2Frame = Frame(self.app)
        additionalToolsRow2Frame.pack(pady=5)
        Button(additionalToolsRow2Frame, text="Quit", bootstyle="primary", cursor="hand2", command=self.quitApp).grid(row=0, column=0, padx=5)

        
    def settingsScreen1(self):

        self.clearScreen()

        Label(self.app, text="Settings", font=self.FONT_TITLE).pack(pady=(10, 5))

        controllerIpFrame = Frame(self.app)
        controllerIpFrame.pack()
        Label(controllerIpFrame, text="Controller IP:", font=self.FONT_DEFAULT).pack(padx=5, side=LEFT)
        controllerIpEntry = Entry(controllerIpFrame)
        controllerIpEntry.pack(padx=5)

        # Show settings
        controllerIpEntry.insert(0, self.settings["controllerIp"])

        controls = Frame(self.app, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        backBtn = Button(controls, text="Exit", bootstyle="primary", width=10, cursor="hand2", command=self.mainScreen1)
        backBtn.pack(side="left")
        nextBtn = Button(controls, text="Save", bootstyle="primary", width=10, cursor="hand2", command=partial(self.settingsScreenSave, controllerIpEntry))
        nextBtn.pack(side="right")

    def settingsScreenSave(self, controllerIpEntry):

        self.settings["controllerIp"] = controllerIpEntry.get()

        self.saveSettings()
        self.mainScreen1()

    def factoryResetPopup(self):

        popup = Toplevel("Are you sure?")
        popup.geometry(f"{self.POPUP_WIDTH}x{self.POPUP_HEIGHT}")

        Label(popup, text="This will reset all the settings and force you to run a controller setup on next startup. Are you sure?", font=self.FONT_DEFAULT, justify=CENTER, wraplength=self.POPUP_WIDTH-20).pack(pady=10)

        controls = Frame(popup, width=self.WINDOW_WIDTH, height=30)
        controls.pack_propagate(False)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)
        Button(controls, text="No", bootstyle="primary", width=10, cursor="hand2", command=popup.destroy).pack(side="left")
        Button(controls, text="Yes", bootstyle="primary", width=10, cursor="hand2", command=self.doFactoryReset).pack(side="right")

        popup.transient()
        popup.grab_set()
        self.app.wait_window(popup)

        # TODO

    def doFactoryReset(self):

        self.factoryReset = True
        self.quitApp()
        

    
       
        

    
    def run(self):
        
        if self.settings["onNextStartup"] == "setup":

            self.setupScreen1()
            self.app.mainloop()

        elif self.settings["onNextStartup"] == "run":

            self.mainScreen1()
            self.app.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()
