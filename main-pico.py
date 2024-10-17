import network, socket, time, _thread, os, sh1106, utime, gc
from config import *
from machine import Pin, SoftI2C, reset

def show_ram():
    while True:
        gc.collect()
        print(f"RAM Usage: {gc.mem_free()}/{gc.mem_free()+gc.mem_alloc()}MB")
        time.sleep(1)
    
def displayCenteredText(texts):
    """Used for displaying centered text on the OLED display."""
    
    if display_found:
        display.fill(0)
        textStartingY = int(HEIGHT / 2 - (len(texts) * 7 + (len(texts) - 1) * 2) / 2)
        for text in texts:
            textStartingX = int(WIDTH / 2 - (len(text) * 6 + (len(text) - 1) * 2) / 2)
            display.text(text, textStartingX, textStartingY, 1)
            textStartingY += 9
        display.show()

def end_and_log(source, text):
    """Creates an infinite inescapable loop, writes the error into a log file
       and displays some info on screen."""
    
    date = time.localtime(time.time())
    error_time = f"{date[2]}-{date[1]}-{date[0]} {date[3]}:{date[4]}:{date[5]}"
    log = f"""
{error_time}, {source}:
{text}
"""
    with open("log.txt", "r") as f:
        log = f.read() + log
    with open("log.txt", "w") as f:
        f.write(log)
        
    if display_found:
        displayCenteredText(["Error occured in", "'" + source + "'.", "Check log.txt", "for more info."])
        while True:
            time.sleep(0.01)
    else:
        while True:
            led.value(not led.value())
            time.sleep(0.5)

def set_screen(screen):
    global display_found, network_info
    
    if display_found:
        if screen == -3:
            displayCenteredText(["Welcome!"])
        
        elif screen == -2.1:
            displayCenteredText(["Connecting wifi.", "Please wait."])
            
        elif screen == -2.2:
            displayCenteredText(["Connecting wifi.", "Please wait.."])
            
        elif screen == -2.3:
            displayCenteredText(["Connecting wifi.", "Please wait..."])
            
        elif screen == -1:
            displayCenteredText(["Connected!"])
            
        elif screen == 0:
            displayCenteredText(["IP:", network_info[0]])
        
        elif screen == 1:
            displayCenteredText(["Password:", ACCESS_PASSWORD])
        
    
def next_screen():
    global screen
    screen += 1
    
    if screen > 1:
        screen = 0
        
    set_screen(screen)
    
def check_button():
    global screen
    button_press_time = time.time()
    button_ready = True
    
    while True:   
        if button.value() == 0 and button_ready == True:
            button_ready = False
            next_screen()
            button_press_time = time.time()
            button_reset_time = button_press_time + 3
            while button.value() == 0:
                if time.time() > button_reset_time:
                    displayCenteredText(["Restarting in", "3"])
                    time.sleep(1)
                    displayCenteredText(["Restarting in", "2"])
                    time.sleep(1)
                    displayCenteredText(["Restarting in", "1"])
                    time.sleep(1)
                    reset()
                time.sleep(0.01)
            
        elif button.value() == 1 and button_ready == False:
            button_ready = True
            
        if button_press_time + 5 < time.time():
            if display_found:
                display.fill(0)
                display.show()
            screen = 1
        
        time.sleep(0.01)

def resp_content_type(filename):
    """Generates the Content-Type header for an HTML response."""

    _, ext = filename.rsplit('.', 1)
    ext += ";"

    # Content-Type: text/html; charset=UTF-8
    #               ↑↑↑↑
    content_type_prefixes = [
        ("css;html;js;", "text"),
        ("inco;pg;jpg;jpeg;webp;svg;gif;", "image")
    ]

    # Content-Type: text/html; charset=UTF-8  (include only if it's different than the file extension)
    #                    ↑↑↑↑
    content_type_suffixes = [
        ("ico;", "x-icon"),
        ("jpg;", "jpeg")
    ]
    
    # Content-Type: text/html; charset=UTF-8  (include only when needed)
    #                        ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
    content_type_encodings = [  
        ("css;html;js;", "; charset=UTF-8")
    ]

    content_type_prefix, content_type_suffix, content_type_encoding = "", ext[:-1], ""
    
    for prefix in content_type_prefixes:
        if ext in prefix[0]: content_type_prefix = prefix[1]

    for suffix in content_type_suffixes:
        if ext in suffix[0]: content_type_suffix = suffix[1]

    for encoding in content_type_encodings:
        if ext in encoding[0]: content_type_encoding = encoding[1]

    content_type = content_type_prefix + "/" + content_type_suffix + content_type_encoding

    return content_type

def resp_date():
    """Generates the Date header for an HTML response."""

    current_time = utime.gmtime()

    date = "{:s}, {:02d} {:s} {:d} {:02d}:{:02d}:{:02d} GMT".format(
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][current_time[6]],
        current_time[2],
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][current_time[1] - 1],
        current_time[0],
        current_time[3],
        current_time[4],
        current_time[5]
    )
    
    return date

def resp_construct(content_type, body, status=200):
    """Generates the HTML response."""

    if status == 200:
        headers = [
            b"HTTP/1.1 200 OK",
            b"Content-Type: " + content_type.encode(),
            b"Content-Length: " + str(len(body)).encode(),
            b"Date: " + resp_date().encode(),
            b"Connection: keep-alive",
            b"",
            body
            ]
        
    elif status == 204:
        headers = [
            b"HTTP/1.1 204 No Content",
            b"Date: " + resp_date().encode(),
            b"Connection: close"
            ]
        
    elif status == 401:
        headers = [
            b"HTTP/1.1 401 Unauthorized",
            b"Content-Type: " + content_type.encode(),
            b"Content-Length: " + str(len(body)).encode(),
            b"Date: " + resp_date().encode(),
            b"Connection: close",
            b"",
            body
            ]
    
    elif status == 404:
        headers = [
            b"HTTP/1.1 404 Not Found",
            b"Date: " + resp_date().encode(),
            b"Connection: close"
            ]
        
    elif status == 409:
        headers = [
            b"HTTP/1.1 409 Conflict",
            b"Content-Type: " + content_type.encode(),
            b"Content-Length: " + str(len(body)).encode(),
            b"Date: " + resp_date().encode(),
            b"Connection: close",
            b"",
            body
            ]
    
    response = headers[0]
    for i in range(len(headers)-1):
        response += b"\r\n" + headers[i+1]

    return response

def read_file(path):
    """Reads a file... Yep."""
    with open(path, "rb") as f:

        return f.read()

def handle_request(conn, addr):
    """Handles the HTML request according to its method."""
    
    # If DEBUGGING variable is True, requests and responses will be printed into the terminal.
    
    if DEBUGGING: print("handling request...")
    
    if DEBUGGING: print('\n-----------\nGot a connection from', addr)

    request = conn.recv(1024).decode()
    
    if DEBUGGING: print("-----------\nRequest: \n", request)

    request = request.split("\r\n")
    req_method, req_path, _ = request[0].split(" ")

    if req_method == "GET":
        req_path = req_path[1:]
        if req_path == "": req_path = "index.html"
            
        content_type = resp_content_type(req_path)
        try:
            req_body = read_file(req_path)
            response = resp_construct(content_type, req_body)
        except FileNotFoundError:
            response = resp_construct(None, None, 404)

        if DEBUGGING: 
            try:
                printable_response = response.decode()

            except UnicodeDecodeError:
                printable_response = response

            if len(printable_response) > 2000:
                print("-----------\nResponse: \n", printable_response[:2000], "...")
            else:
                print("-----------\nResponse: \n", printable_response)

    if req_method == "POST":
        req_body = request[-1]
        
        data = eval(req_body)

        # If the user tries to access admin settings
        if data["type"] == "adminSettingsAccessAttempt":

            if data["data"] == ADMIN_PASSWORD:
                admin_access.append(addr[0])
                response = resp_construct("text/plain", "adminAccessGranted", 200) 

            else:
                response = resp_construct("text/plain", "adminAccessDenied", 401) 

        # If the address of the request matches with the address of the connected user:
        # (the user is authenticated and able to interact with the device)
        elif occupied_by == addr[0]:
        
            if data["type"] == "powerButton":
                if data["data"] == "press":
                    opto_input.value(1)
                    led.value(1)
                    
                elif data["data"] == "release":
                    opto_input.value(0)
                    led.value(0)
                    
            if data["type"] == "disconnected":
                occupied_by = None

            response = resp_construct(None, None, 204)
        
        # If no one is connected:
        elif not occupied_by:
            
            # If someone tries to connect:
            if data["type"] == "accessAttempt" and ACCESS_MODE == "password":
                if data["data"] == ACCESS_PASSWORD:
                    occupied_by = addr[0]
                    response = resp_construct("text/plain", "accessGranted", 200)
                else:
                    response = resp_construct("text/plain", "accessDenied", 401)
            
            if data["type"] == "accessAttempt" and ACCESS_MODE == "whitelist":
                if addr[0] in ACCESS_WHITELIST:
                    occupied_by = addr[0]
                    response = resp_construct("text/plain", "accessGranted", 200)
                else:
                    response = resp_construct("text/plain", "accessDenied", 401)
                    
        # If none of the above happens
        # (meaning that someone else is using the device)
        else:
            response = resp_construct("text/plain", "occupied", 409)
        
    conn.send(response)
    conn.close()

# Width and height of OLED display
WIDTH, HEIGHT = 128, 64

# Pin numbers
SCL = 20
SDA = 21
OPTO = 16
BUTTON = 15

# Screen number
screen = 0

# Initializing pins
led = Pin("LED", Pin.OUT)
button = Pin(BUTTON, Pin.IN, Pin.PULL_UP)
opto_input = Pin(OPTO, Pin.OUT)

# Allowed access modes
ALLOWED_ACCESS_MODES = ["password", "whitelist"]

# Initializing the display
i2c = SoftI2C(scl=Pin(SCL), sda=Pin(SDA))
try:
    display = sh1106.SH1106_I2C(WIDTH, HEIGHT, i2c)
    display.flip()
    display_found = True
except OSError:
    led.value(1)
    display_found = False
    

# Initial check for errors in config.py
if ACCESS_MODE not in ALLOWED_ACCESS_MODES:
    end_and_log("config.py", "Variable ACCESS_MODE is set to an unknown value. Check spelling, make sure it is written in lowercase.")
    
elif ACCESS_MODE == "whitelist" and not ACCESS_WHITELIST:
    end_and_log("config.py", "Variable ACCESS_WHITELIST is empty. If variable ACCESS_MODE is set to \"whitelist\", this variable is mandatory.")
    
elif ACCESS_MODE == "password":
    if not ACCESS_PASSWORD:
        end_and_log("config.py", "Variable ACCESS_PASSWORD is empty. If variable ACCESS_MODE is set to \"password\", this variable is mandatory.")
    elif len(ACCESS_PASSWORD) > 16:
        end_and_log("config.py", "Value in a variable ACCESS_PASSWORD has more characters than allowed (16).")

if not ADMIN_PASSWORD:
    end_and_log("config.py", "Variable ADMIN_PASSWORD is empty.")

# Starts
set_screen(-3)
time.sleep(2)
set_screen(-2.1)

screen = -2.1

# Connect to WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print(wlan.scan())

if WIFI_PASSWORD == "":
    wlan.connect(WIFI_NAME)
else:
    wlan.connect(WIFI_NAME, WIFI_PASSWORD)



# Wait for Wi-Fi connection
while 1:
    if wlan.status() >= 3:
        break
    if not display_found:
        led.value(not led.value())
    time.sleep(1)
    if screen == -2.1:
        screen = -2.2
    elif screen == -2.2:
        screen = -2.3
    else:
        screen = -2.1
    set_screen(screen)


# Check if connection is successful
if wlan.status() == 3:
    set_screen(-1)
    network_info = wlan.ifconfig()
    led.value(0)
    time.sleep(0.13)
    if not display_found:
        for i in range(3):
            led.value(1)
            time.sleep(0.13)
            led.value(0)
            time.sleep(0.13)
        
time.sleep(1.5)
set_screen(0)
screen = 0

# Set up socket and start listening
s_addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(s_addr)
s.listen()

_thread.start_new_thread(check_button, ())

occupied_by = None
admin_access = []

# Main loop to listen for connections
while True:

    conn, addr = s.accept()
    if DEBUGGING: print("connection accepted")
    _thread.start_new_thread(handle_request, (conn, addr))
