$(document).ready(() => {
    
    async function post (data, type) {

        // This function is used to send a POST request to the server/app

        let message = {data: data, type: type}
    
        let something = await fetch(`http://${target}:5000`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(message)
        })
        .then(response => response.text())
        .catch(error => error);

        return something;
    }

    function connected () {

        // Shows the connect screen and initiates the timer for inactive logout

        connectScreen.css("display", "none");
        main.css("display", "flex");

        inactiveLogout();
        $(document).on("touchstart", () => {
            inactiveLogout();
        })
        $(document).on("touchmove", () => {
            inactiveLogout();
        })
        $(document).on("touchend", () => {
            inactiveLogout();
        })
        

        // NOTDONE Starts requesting the screen of target device
        if (screenshareInterval != 0) {
            updateScreen = setInterval(() => {
                screenshare();
            }, screenshareInterval);
        }
    }

    async function screenshare () {
        let screenshot_bytes = await post("empty", "showScreen");
        const img = new Image();
        img.src = "data:image/png;base64," + screenshot_bytes;
        screenshare_screen.empty();
        $(screenshare_screen).append(img);
    }

    async function connectButton () {

        // After pressing the connect button, sends a request with a password.
        // Also handles any errors returned from server

        connect.prop("disabled", true);
        connect.css("opacity", 0.5);
        loading.css("opacity", 1);
        connectError.text("");

        let password = passwordInput.val();
        let response;

        let ttl = new Promise((_, reject) => {
            setTimeout(() => reject("ttl reached"), 7000)
        })

        try {
            response = await Promise.race([post(password, "connect"), ttl])
        } catch (error) {
            response = error
        }
        
        if (response === "connect success") {
            connected();

        } else if (response === "connect failed") {
            connectError.text("Incorrect password");

        } else if (response === "occupied") {
            connectError.text("Target device is occupied");

        } else if (response.includes("Failed to fetch")) {
            connectError.text("Device with specified IP not found");

        } else if (response === "ttl reached") {
            connectError.text("Target device refused connection");

        }
    
        connect.prop("disabled", false);
        connect.css("opacity", 1);
        loading.css("opacity", 0);
    }

    function handleOrientationChange(mql) {

        // Handles the change of screen orientation on mobile devices

        if (mql.matches) {
            // Portrait
            landscapeScreen.css("display", "none")
        } else {
            // Landscape
            landscapeScreen.css("display", "flex")
        }
    }

    function inactiveLogout () {

        // A timer that forces the client to disconnect after 60s of inactivity

        clearTimeout(logoutTime);
        logoutTime = setTimeout(() => {
            post("empty", "inactive dc")
            connectScreen.css("display", "flex")
            main.css("display", "none")
            $(document).off("touchstart");
            $(document).off("touchmove");
            $(document).off("touchend");
            connectError.text("Disconnected for inactivity.")
            clearInterval(updateScreen);
            menuState = 0;
            menu.css("left", "-100vw");
        }, 60000);
    }

    // Disconnects the client if it closes the browser or refreshes the page
    $(window).on("beforeunload", () => {
        post("empty", "browser refresh")
    });
    
    // Force scroll to the top
    setTimeout(() => {
        window.scrollTo(0, 0)
    }, 100);

    
    let userAgent = navigator.userAgent;
    let target_w_port = new URL(window.location.href).origin.substring(7);
    let target = target_w_port.substring(0, target_w_port.length - 6)
    let menuState = 0;
    let mouseUpdateInterval = 100;
    let screenshareInterval = 200;
    let mousepadPostOnCooldown = false;
    let logoutTime, updateScreen, initialX, initialY, keyboardPreviousValue, keyboardCurrentValue;
    
    const loading = $(".loading");
    const passwordInput = $("#password");
    const connectError = $(".connect-error");
    const connectScreen = $(".connect-screen");
    const triangleTopLeft = $(".triangle-top-left");
    const triangleBottomRight = $(".triangle-bottom-right");
    const main = $(".main");
    const notAndroidScreen = $(".not-android-screen");
    const landscapeScreen = $(".landscape-screen");
    const keyboard = $("#keyboard");
    const menuButton = $(".menu-button");
    const menu = $(".menu");
    const disconnect = $("#disconnect");
    const connect = $(".connect");
    const saveMenu = $("#menu-save");
    const screenshareIntervalInput = $("#screenshare-interval-input");
    const mouseUpdateIntervalInput = $("#mouse-update-interval-input");
    const touchpad = $(".touchpad");
    const sensitivity = $("#sensitivity");
    const sensitivityDisplay = $(".sensitivity-display");
    const screenshare_screen = $(".screen");
    const hotkeys_array = ["Enter", "Backspace", "Esc", "Caps Lock"];
    const hotkeys_div = $(".hotkeys");


    if (/Android/.test(userAgent) || /iPhone/.test(userAgent)) {
        // Is android/Iphone
        // Create a media query for portrait orientation
        let portraitMediaQuery = window.matchMedia("(orientation: portrait)");
        portraitMediaQuery.addListener(handleOrientationChange);
        
        // Initial orientation check
        handleOrientationChange(portraitMediaQuery);

    } else {
        // Isn't android/Iphone
        // Shows an alert, informing that this app can only
        // be used on mobile devices
        
        // main.css("display", "none")
        // connectScreen.css("display", "none")
        // landscapeScreen.css("display", "none")
        // notAndroidScreen.css("display", "flex")
    }


    // Connect and disconnect buttons
    connect.click(connectButton);

    disconnect.click(() => {
        clearTimeout(logoutTime);
        clearInterval(updateScreen);
        post("empty", "dc");
        connectScreen.css("display", "flex");
        main.css("display", "none");
        menuState = 0;
        menu.css("left", "-100vw");
    })


    // Hotkeys 
    for (let index = 0; index < hotkeys_array.length; index++) {
        const hotkey_name = hotkeys_array[index];
        
        const hotkey_button = $("<button>", {
            text: hotkey_name,
            click: () => {
                post(hotkey_name, "hotkeyPress");
            }
        });
        hotkeys_div.append(hotkey_button);
    }


    // Touchpad sensitivity
    sensitivityDisplay.text(Number(sensitivity.val()) / 100);

    sensitivity.on("input", () => {
        sensitivityDisplay.text(Number(sensitivity.val()) / 100);
    });


    // Touchpad    
    $(touchpad).on("touchstart", (event) => {
        let touch = event.originalEvent.touches[0];
        initialX = touch.clientX;
        initialY = touch.clientY;
        post("empty", "mousepadTouch");
    });

    $(touchpad).on("touchmove", (event) => {
        let touch = event.originalEvent.touches[0];
        let x = Math.floor(touch.clientX - initialX) * (Number(sensitivity.val()) / 100);
        let y = Math.floor(touch.clientY - initialY) * (Number(sensitivity.val()) / 100);
        if (mousepadPostOnCooldown === false) {
            mousepadPostOnCooldown = true;
            post(`${x}/${y}`, "mousepadMove");
            setTimeout(() => {
                mousepadPostOnCooldown = false;
            }, mouseUpdateInterval);
        }
    });

    $(touchpad).on("touchend", () => {
        post("empty", "mousepadRelease");
    });
});