# All variables are mandatory, unless stated otherwise.

# Leave the WIFI_PASSWORD empty, if the WiFi is free
WIFI_NAME = "TP-Link_2.4GHz_27E704"
WIFI_PASSWORD = ""

# Set the ACCESS_MODE variable accordingly:
# "password" - When using this mode, the
#    user will be prompted to enter a password,
#    which can be set in a variable ACCESS_PASSWORD.
# "whitelist" - When using this mode, only
#    users with specified IP address will be
#    able to use this device. If this mode is set,
#    the user's IP address will be displayed on
#    the site when they will try to connect. Add
#    this IP address to a list in a
#    variable ACCESS_WHITELIST.
ACCESS_MODE = "password"

# The ACCESS_PASSWORD variable is only mandatory if the
# ACCESS_MODE variable is set to "password".
# The password can't be longer than 16 characters.
# This password is also displayed on the screen of the
# device if the ACCESS_MODE variable is set to "password".
ACCESS_PASSWORD = "Ahoj123."

# The ACCESS_WHITELIST variable is only mandatory if the
# ACCESS_MODE variable is set to "whitelist".
# Add the IPs inside the square brackets as shown.
ACCESS_WHITELIST = ["white.list.ip.1", "white.list.ip.2"]

# The ADMIN_PASSWORD variable is used as a password
# for remotely accessing this "config.py" file.
# The password can't be longer than 16 characters.
ADMIN_PASSWORD = "AdminPassword123"

# Set the DEBUGGING variable to True, if you want to see
# the requests and responses printed into the consoles, etc.
# Otherwise, set to False.
DEBUGGING = False
