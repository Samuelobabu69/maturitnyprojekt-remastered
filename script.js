$(document).ready(() => {

    async function request (method, type, data, target) {

        // This function is used to send a POST request to the server/app

        if (target == "pc") {
            target = computerIp
        }
        
        if (target == "mc") {
            target = serverIp
        }

        let message = {type: type, data: data}
    
        let something = await fetch(`http://${target}:80`, {
            method: method,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(message)
        })
        .then(response => response.text())
        .catch(error => error);

        return something;
    }

    function inactiveLogout () {

        // A timer that forces the client to disconnect after 60s of inactivity

        clearTimeout(logoutTimeout);
        logoutTimeout = setTimeout(() => {
            request("POST", "disconnect", "None", "mc");
            loginScreen.css("display", "flex");
            controlScreen.css("display", "none");
            $(document).off("touchstart", inactiveLogout);
            $(document).off("touchmove", inactiveLogout);
            $(document).off("touchend", inactiveLogout);
            loginError.text("Disconnected for inactivity.")
            settingsHidden = true;
            settingsScreen.css("left", "-100vw");
        }, 5000);
    }
    

    

    function buttonConfirmation (btnElem, func, timeToConfirm = 1500) {

        if (btnElem.data("readytoconfirm") == undefined) {
            btnElem.data("readytoconfirm", true);
            btnElem.data("beforetext", btnElem.text());
            btnElem.text("Confirm");
            let confirmationTimeout = setTimeout(() => {
                btnElem.text(btnElem.data("beforetext"));
                btnElem.removeData("readytoconfirm beforetext confirmationtimeout")
            }, timeToConfirm);
            btnElem.data("confirmationtimeout", confirmationTimeout);
        } else {
            btnElem.text(btnElem.data("beforetext"));
            clearTimeout(btnElem.data("confirmationtimeout"));
            btnElem.removeData("readytoconfirm beforetext confirmationtimeout")
            func();
        }
    }

    function animateButton (btnElem) {
        btnElem.css("transition", "transform 0.3s")
        btnElem.on("touchstart", () => {
            btnElem.css("transform", "scale(0.9)")
        })

        btnElem.on("touchend", () => {
            btnElem.css("transform", "scale(1)")
        })
    }
    
    $(window).on("beforeunload", () => {
        request("POST", "disconnect", "None", "mc");
    })

    



    
    /// Login ///
    
    const showPasswordBtn = $(".show-password-btn");
    const showPasswordBtnImg = $(".show-password-btn img");
    const accessPasswordLoginInput = $("#access-password-login-input");
    const connectButton = $(".connect-btn");
    const loginScreen = $(".login");
    const controlScreen = $(".control");
    const loginError = $(".login-error");

    let logoutTimeout;
    
    // This SERVER_IP string is replaced by the server with
    // it's actual IP address
    let serverIp = "SERVER_IP";

    // This COMPUTER_IP string is replaced by the server with
    // the IP address of the computer
    let computerIp = "COMPUTER_IP";
    
    // Button to show/hide password on the login page
    showPasswordBtn.click(() => {
        if (accessPasswordLoginInput.attr("type") === "password") {
            accessPasswordLoginInput.attr("type", "text");
            showPasswordBtnImg.attr("src", "https://github.com/Samuelobabu69/maturitnyprojekt-remastered/blob/main/assets/show-icon.png?raw=true");
        } else {
            accessPasswordLoginInput.attr("type", "password");
            showPasswordBtnImg.attr("src", "https://github.com/Samuelobabu69/maturitnyprojekt-remastered/blob/main/assets/hide-icon.png?raw=true");
        }

        accessPasswordLoginInput.focus();

    })

    connectButton.click(async () => {
        connectButton.prop("disabled", true);
        connectButton.css({
            "border": "3px solid var(--colortext)",
            "border-top": "2px solid var(--colortext)",
            "border-right": "2px solid var(--colortext)"
        });
        loginError.text("")

        let password = accessPasswordLoginInput.val();
        let response;

        let ttl = new Promise((_, reject) => {
            setTimeout(() => reject("ttlReached"), 7000)
        })

        try {
            response = await Promise.race([request("POST", "accessAttempt", password, "mc"), ttl])
        } catch (error) {
            response = error
        }

        console.log(response);

        if (response == "accessGranted") {
            loginScreen.css("display", "none");
            controlScreen.css("display", "block");

            inactiveLogout()
            $(document).on("touchstart touchmove touchend", inactiveLogout);

        } else if (response == "accessDenied") {
            loginError.text("Incorrect password");
        } else if (response == "occupied") {
            loginError.text("Device is occupied");
        } else if (response == "ttlReached") {
            loginError.text("TTL reached");
        } else {
            loginError.text("Unknown error");
        }

        connectButton.prop("disabled", false);
        connectButton.css({
            "border": "5px solid var(--colortext)",
            "border-top": "none",
            "border-right": "none"
        });

    })

    /// Power Button ///

    const powerButtonOpen = $(".power-button");
    const powerButtonClose = $(".power-close-button");
    const powerMenu = $(".power-menu-wrapper");
    const powerButton = $("#power-button");
    let powerMenuHidden = true;
    
    powerButtonOpen.on("touchstart", () => {
        if (powerMenuHidden) {
            powerMenuHidden = false;
            powerMenu.css("bottom", "350px");
            powerButtonOpen.css("bottom", "190px");
            powerButtonClose.css("bottom", "265px")
        } 
    });

    powerButtonClose.on("touchstart", () => {
        if (!powerMenuHidden) {
            powerMenuHidden = true;
            powerMenu.css("bottom", "0");
            powerButtonClose.css("bottom", "190px");
            powerButtonOpen.css("bottom", "265px")
        } 
    });

    powerButton.on('contextmenu touchstart', (e) => {
        e.preventDefault(); 
    })

    powerButton.on("touchstart", () => {
        request("POST", "powerButton", "press", "pc");
        
        powerButton.css({
            "border": "3px solid var(--colortext)",
            "border-top": "2px solid var(--colortext)",
            "border-right": "2px solid var(--colortext)"
        });
    })

    powerButton.on("touchend", () => {
        request("POST", "powerButton", "release", "pc");
        
        powerButton.css({
            "border": "5px solid var(--colortext)",
            "border-top": "none",
            "border-right": "none"
        });
    })

    

    /// Mousepad ///

    const mousepad = $(".mousepad");
    let mousepadPostOnCooldown = false;
    let mouseUpdateInterval = 50;
    let initialX, initialY, mouseSensitivity;

    mousepad.on("touchstart", (event) => {
        let touch = event.originalEvent.touches[0];
        initialX = touch.clientX;
        initialY = touch.clientY;
    });

    mousepad.on("touchmove", (event) => {
        let touch = event.originalEvent.touches[0];
        let x = Math.floor(touch.clientX - initialX) * mouseSensitivity;
        let y = Math.floor(touch.clientY - initialY) * mouseSensitivity;
        if (mousepadPostOnCooldown === false) {
            mousepadPostOnCooldown = true;
            console.log(`${x}/${y}`);
            setTimeout(() => {
                mousepadPostOnCooldown = false;
            }, mouseUpdateInterval);
        }
    });

    mousepad.on("touchend", () => {
        
    });

    const keyboard = $(".keyboard");
    const keyboardToMousepadSwitch = $(".keyboard-to-mousepad-switch");
    const mousepadToKeyboardSwitch = $(".mousepad-to-keyboard-switch");
    let keyboardHidden = true;

    mousepadToKeyboardSwitch.on('contextmenu touchstart', function (e) {
        e.preventDefault(); 
    })

    keyboardToMousepadSwitch.on('contextmenu touchstart', function (e) {
        e.preventDefault(); 
    })

    mousepadToKeyboardSwitch.on("touchstart", () => {
        if (keyboardHidden) {
            keyboardHidden = false;
            keyboard.css("bottom", "0");
            mousepadToKeyboardSwitch.css("bottom", "190px");
            keyboardToMousepadSwitch.css("bottom", "265px")
        } 
    });

    keyboardToMousepadSwitch.on("touchstart", () => {
        if (!keyboardHidden) {
            keyboardHidden = true;
            keyboard.css("bottom", "-260px");
            keyboardToMousepadSwitch.css("bottom", "190px");
            mousepadToKeyboardSwitch.css("bottom", "265px")
        } 
    });
    


    /// Keyboard ///

    const keyboardKeys = $(".key");
    const shiftAffectedKeys = $(".shift-affected-key");
    const aftertapKeys = $(".aftertap-key");

    
    const keyboardLetters = $(".keyboard-letters");
    const keyboardNumbers = $(".keyboard-numbers");
    const keyboardSymbols = $(".keyboard-symbols");
    const LToNKey = $(".l-to-n-key");
    const NToLKey = $(".n-to-l-key");
    const NToSKey = $(".n-to-s-key");
    const SToNKey = $(".s-to-n-key");
    const shiftKey = $(".shift-key");
    const shiftKeyImg = $(".shift-key img");

    // Keys that have alternate keys when you hold them
    let alternateKeys = [
        ["e", "é"],
        ["r", "ŕ"],
        ["t", "ť"],
        ["z", "ž"],
        ["u", "ú"],
        ["i", "í"],
        ["o", "ó ô"],
        ["a", "á ä"],
        ["s", "š"],
        ["d", "ď"],
        ["l", "ľ ĺ"],
        ["y", "ý"],
        ["c", "č"],
        ["n", "ň"],
        ["E", "É"],
        ["R", "Ŕ"],
        ["T", "Ť"],
        ["Z", "Ž"],
        ["U", "Ú"],
        ["I", "Í"],
        ["O", "Ó Ô"],
        ["A", "Á Ä"],
        ["S", "Š"],
        ["D", "Ď"],
        ["L", "Ľ Ĺ"],
        ["Y", "Ý"],
        ["C", "Č"],
        ["N", "Ň"]
    ]
    let shiftState = 0;
    let keyAlternateSelectorIndex = 0;
    let typingAlternate = false;
    let keyToSend;

    function findAlternateKey (key) {
        // Finds alternate key in the alternateKeys array
        for (let index = 0; index < alternateKeys.length; index++) {
            const pair = alternateKeys[index];

            if (pair[0] === key) {
                return pair[1];
            }
        }
        return false;
    }

    // Keyboard keys
    for (let index = 0; index < aftertapKeys.length; index++) {
        const key = aftertapKeys.eq(index);
        const keyAftertapElem = $(`<div class="key-aftertap"></div>`);
        
        let keyHoldTimer, absoluteX, relativeX; 

        key.on("touchstart", () => {
            keyAftertapElem.text(key.text())
            key.append(keyAftertapElem);

            // Absolute position of the key
            absoluteX = key.offset().left;

            // Happens after half a second of holding the key.
            keyHoldTimer = setTimeout(() => {
                let newWidth;
                let oldWidth = keyAftertapElem.css("width");

                // Finds the alternate key and shows it if there is one
                let alternateKeys = findAlternateKey(keyAftertapElem.text());
                if (alternateKeys) {
                    alternateKeys = alternateKeys.split(" ")
                    typingAlternate = true;

                    newWidth = oldWidth;
                    
                    // Shifting the alternate keys if there are 2 of them,
                    // setting their width and handles the "L exception"
                    if (alternateKeys.length == 2) {
                        newWidth = Number(oldWidth.slice(0, oldWidth.length-2))*2+"px";
                        if (key.attr("data-char") === "l") {
                            keyAftertapElem.css("transform", "translateX(-25%) translateY(-25%)");
                        } else {
                            keyAftertapElem.css("transform", "translateX(25%) translateY(-25%)");
                        }
                    }

                    keyAftertapElem.css("background-color", "var(--colorkeyhold)")
                    keyAftertapElem.css("width", newWidth);
                    keyAftertapElem.empty()
                    
                    // Adds the alternate keys to the display
                    for (let index = 0; index < alternateKeys.length; index++) {
                        const character = alternateKeys[index];
                        const keyAlternateSelector = $(`<div class="key-alternate-selector"></div>`)
                        if (alternateKeys.length == 2) {
                            keyAlternateSelector.css("width", "40%");
                        }
                        if (key.attr("data-char") === "l") {
                            if (index === 1) {
                                keyAlternateSelector.css("background-color", "var(--colorkey)");
                            } 
                        } else if (index === 0) {
                            keyAlternateSelector.css("background-color", "var(--colorkey)");
                        } 
                        
                        keyAlternateSelector.text(character)
                        keyAftertapElem.append(keyAlternateSelector);
                    }
                }
            }, 400);
        });

        key.on("touchmove", (event) => {

            // Handling the selection of alternate keys,
            // if there are 2 or more of them
            if (keyAftertapElem.children().length !== 1) {

                let touch = event.originalEvent.touches[0];
                relativeX = touch.clientX - absoluteX;

                if (key.attr("data-char") === "l") {
                    relativeX = relativeX + 40;
                }
    
                keyAlternateSelectorIndex = Math.floor(relativeX / 40);
                
                // Highlighting the selecting alternate key
                for (let index = 0; index < keyAftertapElem.children().length; index++) {
                    const element = keyAftertapElem.children().eq(index);

                    if (index === 0) {
                        if (keyAlternateSelectorIndex <= index) {
                            element.css("background-color", "var(--colorkey)");
                        } else {
                            element.css("background-color", "transparent");
                        }
                    } else {
                        if (keyAlternateSelectorIndex >= index) {
                            element.css("background-color", "var(--colorkey)");
                        } else {
                            element.css("background-color", "transparent");
                        }
                    }  
                }
            }
        });

        key.on("touchend", () => {

            // Reseting everything
            keyAftertapElem.remove();
            clearInterval(keyHoldTimer)
            keyAftertapElem.css({
                "width": "calc(100%/10)",
                "transform": "translateY(-25%)",
                "background-color": "var(--colorkey)"
            });

            // Detecting the character to send
            keyToSend = key.attr("data-char");
            if (typingAlternate) {
                let alternateKeys = findAlternateKey(keyToSend).split(" ");
                if (alternateKeys.length == 1 || keyAlternateSelectorIndex <= 0) {
                    keyToSend = alternateKeys[0];
                } else if (keyAlternateSelectorIndex >= 1) {
                    keyToSend = alternateKeys[1];
                }

            }
            if (shiftState != 0) {
                keyToSend = keyToSend.toUpperCase();
            }


            // TODO: character sending
            request("POST", "keyPress", keyToSend, "pc")
            console.log(keyToSend)

            typingAlternate = false;
        });

        
    }

    // Preventing the menu from showing up after
    // holding on a key with an image.
    for (let index = 0; index < keyboardKeys.length; index++) {
        const key = keyboardKeys.eq(index);

        key.on('contextmenu touchstart', function (e) {
            e.preventDefault(); 
        })
    }

    // Changing the keys to lower case depending
    // on the shift button state
    for (let index = 0; index < shiftAffectedKeys.length; index++) {
        const key = shiftAffectedKeys.eq(index);
        
        key.on("touchend", () => {
            if (shiftState == 1) {
                shiftState = 0;
                shiftKeyImg.attr("src", "https://github.com/Samuelobabu69/maturitnyprojekt-remastered/blob/main/assets/lower-case.png?raw=true");
                for (let index = 0; index < shiftAffectedKeys.length; index++) {
                    const key = shiftAffectedKeys.eq(index);
                    key.text(key.text().toLowerCase())  
                }
            }
        });
    }

    // Switching between keyboards
    LToNKey.on("touchend", () => {
        keyboardLetters.css("display", "none");
        keyboardNumbers.css("display", "flex");
    });

    NToLKey.on("touchend", () => {
        keyboardLetters.css("display", "flex");
        keyboardNumbers.css("display", "none");
        keyboardSymbols.css("display", "none");
    });

    NToSKey.on("touchend", () => {
        keyboardNumbers.css("display", "none");
        keyboardSymbols.css("display", "flex");
    });

    SToNKey.on("touchend", () => {
        keyboardNumbers.css("display", "flex");
        keyboardSymbols.css("display", "none");
    });

    // Shift key handling
    shiftKey.on("touchend", () => {
        shiftState++;
        if (shiftState == 3) {
            shiftState = 0;
        }

        if (shiftState == 0) {
            shiftKeyImg.attr("src", "https://github.com/Samuelobabu69/maturitnyprojekt-remastered/blob/main/assets/lower-case.png?raw=true");
            for (let index = 0; index < shiftAffectedKeys.length; index++) {
                const key = shiftAffectedKeys.eq(index);
        
                key.text(key.text().toLowerCase())
            }
        } else if (shiftState == 1) {
            shiftKeyImg.attr("src", "https://github.com/Samuelobabu69/maturitnyprojekt-remastered/blob/main/assets/upper-case.png?raw=true");
            for (let index = 0; index < shiftAffectedKeys.length; index++) {
                const key = shiftAffectedKeys.eq(index);
        
                key.text(key.text().toUpperCase())
            }
        } else if (shiftState == 2) {
            shiftKeyImg.attr("src", "https://github.com/Samuelobabu69/maturitnyprojekt-remastered/blob/main/assets/caps-lock.png?raw=true");
        }

        
    });


    /// Settings ///

    const settingsButton = $(".settings-button");
    const settingsButtonImg = $(".settings-button img");
    const settingsBlur = $(".settings-blur");
    const settingsScreen = $(".settings");
    const settingsTabBtns = $(".settings-tab-btn");
    const settingsTabs = $(".settings-tab");

    let settingsHidden = true;
    let settingsTabSelected = 0;
    let settingsTimeout;

    settingsButton.on("touchstart", () => {
        if (settingsHidden) {
            clearTimeout(settingsTimeout);
            settingsHidden = false;
            settingsButtonImg.css("transform", "rotate(360deg)");
            settingsButton.css({
                "bottom": "100%",
                "transform": "translateY(110%)"
            });
            settingsBlur.css("display", "flex");
            settingsTimeout = setTimeout(() => {
                settingsBlur.css("backdrop-filter", "blur(5px)");
            }, 10);
            settingsScreen.css("left", "0");
        } else {
            clearTimeout(settingsTimeout);
            settingsHidden = true;
            settingsButtonImg.css("transform", "rotate(0deg)");
            settingsButton.css({
                "bottom": "270px",
                "transform": "translateY(0%)"
            });
            settingsBlur.css("backdrop-filter", "blur(0px)");
            settingsTimeout = setTimeout(() => {
                settingsBlur.css("display", "none");
            }, 500);
            settingsScreen.css("left", "-100%");
        }
    });

    for (let index = 0; index < settingsTabBtns.length; index++) {
        const settingsTabBtn = settingsTabBtns.eq(index);
        
        settingsTabBtn.click(() => {
            for (let index = 0; index < settingsTabBtns.children().length; index++) {
                const settingsTabBtn = settingsTabBtns.eq(index);
                settingsTabBtn.css("background-color", "transparent");
                
            }

            settingsTabSelected = settingsTabBtn.attr("data-settings-tab-btn");

            settingsTabBtn.css("background-color", "var(--colorbg1)");

            for (let index = 0; index < settingsTabs.length; index++) {
                const settingsTab = settingsTabs.eq(index);
                settingsTab.css("left", "-100%");

                if (index == settingsTabSelected) {
                    settingsTab.css("left", "0");
                }
            }
        });

        if (index == 0) {
            settingsTabBtn.click()
        } 
    }

    /// Settings Apply ///

    let defaultSettings = {
        "animated-background": "running",
        "background-color-1": "#000584",
        "background-color-2": "#0A0172",
        "text-color": "#FFFFFF",
        "keyboard-layout": "qwertz",
        "keyboard-letter-size": "medium",
        "mouse-sensitivity": "100",
        "mouse-update-interval": "50",
        "video-enabled": "true",
        "video-quality": "medium",
        "video-fps": "10"
    }

    if (!localStorage.getItem("settings")) {
        localStorage.setItem("settings", JSON.stringify(defaultSettings));
    }

    let settings = JSON.parse(localStorage.getItem("settings"));

    const animatedBackgroundSwitch = $("#animated-background");
    const backgroundColor1Input = $("#background-color-1");
    const backgroundColor2Input = $("#background-color-2");
    const textColorInput = $("#text-color");
    const keyboardLayoutInput = $("#keyboard-layout");
    const keyboardLetterSizeInput = $("#keyboard-letter-size");
    const mouseSensitivityInput = $("#mouse-sensitivity");
    const mouseSensitivityOutput = $(".mouse-sensitivity-output");
    const videoEnabledInput = $("#video-enabled");
    const videoDisabledOutput = $(".video-disabled");
    const videoQualityInput = $("#video-quality");
    const videoFpsInput = $("#video-fps");
    const bgMoving = $(".bg-moving");
    const saveLocalSettingsBtns = $(".save-local-settings-btn");
    const revertLocalSettingsBtns = $(".revert-local-settings-btn");
    const resetLocalSettingsBtns = $(".reset-local-settings-btn");


    function saveLocalSettings () {
        localStorage.setItem("settings", JSON.stringify(settings))
    }

    function applyLocalSettings () {
        bgMoving.css("animation-play-state", settings["animated-background"]);
        document.documentElement.style.setProperty('--colorbg1', settings["background-color-1"]);
        document.documentElement.style.setProperty('--colorbg2', settings["background-color-2"]);
        document.documentElement.style.setProperty('--colortext', settings["text-color"]);
        mouseSensitivity = (Number(settings["mouse-sensitivity"]) / 100).toFixed(1)
        if (settings["keyboard-letter-size"] == "large") {
            keyboardKeys.css("font-size", "xx-large")
        } else if (settings["keyboard-letter-size"] == "medium") {
            keyboardKeys.css("font-size", "x-large")
        } else if (settings["keyboard-letter-size"] == "small") {
            keyboardKeys.css("font-size", "larger")
        }
        if (settings["keyboard-layout"] == "qwerty" && keyboardKeys.eq(15).attr("data-char") == "z") {
            keyboardKeys.eq(15).attr("data-char", "y");
            keyboardKeys.eq(15).text("y");
            keyboardKeys.eq(30).attr("data-char", "z");
            keyboardKeys.eq(30).text("z");
        } else if (settings["keyboard-layout"] == "qwertz" && keyboardKeys.eq(15).attr("data-char") == "y") {
            keyboardKeys.eq(15).attr("data-char", "z");
            keyboardKeys.eq(15).text("z");
            keyboardKeys.eq(30).attr("data-char", "y");
            keyboardKeys.eq(30).text("y");
        }
        if (shiftState != 0) {
            keyboardKeys.eq(15).text(keyboardKeys.eq(15).text().toUpperCase());
            keyboardKeys.eq(30).text(keyboardKeys.eq(30).text().toUpperCase());
        }

        if (settings["video-enabled"] === "true") {
            videoDisabledOutput.css("display", "none");
        } else {
            videoDisabledOutput.css("display", "flex");
        }

    }

    function showLocalSettings () {
        if (settings["animated-background"] == "running") {
            animatedBackgroundSwitch.prop("checked", true);
        } else {
            animatedBackgroundSwitch.prop("checked", false);
        }
        backgroundColor1Input.val(settings["background-color-1"]);
        backgroundColor2Input.val(settings["background-color-2"]);
        textColorInput.val(settings["text-color"]);
        keyboardLayoutInput.val(settings["keyboard-layout"]);
        keyboardLetterSizeInput.val(settings["keyboard-letter-size"]);
        mouseSensitivityInput.val(settings["mouse-sensitivity"]);
        mouseSensitivityOutput.text((Number(settings["mouse-sensitivity"])/100).toFixed(1))

        let mouseSensitivityInputVal = Number(settings["mouse-sensitivity"]);
        let mouseSensitivityOutputLeftMargin = 0;
        
        if (mouseSensitivityInputVal == 100) {
            mouseSensitivityOutputLeftMargin = 0; 
        } else if (mouseSensitivityInputVal == 500) {
            mouseSensitivityOutputLeftMargin = 90; 
        } else {
            mouseSensitivityOutputLeftMargin = (mouseSensitivityInputVal - 100) / 400 * 90;
        }
        
        mouseSensitivityOutput.css("margin-left", mouseSensitivityOutputLeftMargin + "%");
        if (settings["video-enabled"] === "true") {
            videoEnabledInput.prop("checked", true)
        } else {
            videoEnabledInput.prop("checked", false)
        }
        videoQualityInput.val(settings["video-quality"]);
        videoFpsInput.val(settings["video-fps"]);

        applyLocalSettings();
    }

    function resetLocalSettings () {
        localStorage.setItem("settings", JSON.stringify(defaultSettings));
        settings = JSON.parse(localStorage.getItem("settings"));
        showLocalSettings();
    }

    function revertLocalSettings () {
        settings = JSON.parse(localStorage.getItem("settings"));
        showLocalSettings();
    }


    showLocalSettings()


    for (let index = 0; index < saveLocalSettingsBtns.length; index++) {
        const btn = saveLocalSettingsBtns.eq(index);
        animateButton(btn);
        btn.click(() => {
            buttonConfirmation(btn, saveLocalSettings, 1500);
        })
    }

    for (let index = 0; index < resetLocalSettingsBtns.length; index++) {
        const btn = resetLocalSettingsBtns.eq(index);
        animateButton(btn);
        btn.click(() => {
            buttonConfirmation(btn, resetLocalSettings, 1500)
        })
    }

    for (let index = 0; index < revertLocalSettingsBtns.length; index++) {
        const btn = revertLocalSettingsBtns.eq(index);
        animateButton(btn);
        btn.click(() => {
            buttonConfirmation(btn, revertLocalSettings, 1500)
        })
    }


    animatedBackgroundSwitch.change(() => {
        if (!animatedBackgroundSwitch.prop("checked")) {
            settings["animated-background"] = "paused";
        } else {
            settings["animated-background"] = "running";
        }
        applyLocalSettings();
    })
    backgroundColor1Input.change(() => {
        settings["background-color-1"] = backgroundColor1Input.val();
        applyLocalSettings();
    })
    backgroundColor2Input.change(() => {
        settings["background-color-2"] = backgroundColor2Input.val();
        applyLocalSettings();
    })
    textColorInput.change(() => {
        settings["text-color"] = textColorInput.val();
        applyLocalSettings();
    });
    keyboardLayoutInput.change(() => {
        settings["keyboard-layout"] = keyboardLayoutInput.val();
        applyLocalSettings();
    });                                 
    keyboardLetterSizeInput.change(() => {
        settings["keyboard-letter-size"] = keyboardLetterSizeInput.val();
        applyLocalSettings();
    });
    mouseSensitivityInput.on("input", () => {
        let mouseSensitivityInputVal = mouseSensitivityInput.val();
        let mouseSensitivityOutputLeftMargin = 0;
        
        if (mouseSensitivityInputVal == 100) {
            mouseSensitivityOutputLeftMargin = 0; 
        } else if (mouseSensitivityInputVal == 500) {
            mouseSensitivityOutputLeftMargin = 90; 
        } else {
            mouseSensitivityOutputLeftMargin = (mouseSensitivityInputVal - 100) / 400 * 90;
        }
        
        mouseSensitivityOutput.css("margin-left", mouseSensitivityOutputLeftMargin + "%");
        mouseSensitivityOutput.text((Number(mouseSensitivityInputVal)/100).toFixed(1))
        
    });
    mouseSensitivityInput.change(() => {
        settings["mouse-sensitivity"] = mouseSensitivityInput.val();
        applyLocalSettings();
    });
    videoEnabledInput.change(() => {
        settings["video-enabled"] = videoEnabledInput.prop("checked") + "";
        applyLocalSettings();
    })
    videoQualityInput.change(() => {
        settings["video-quality"] = videoQualityInput.val();
        applyLocalSettings();
    });
    videoFpsInput.change(() => {
        settings["video-fps"] = videoFpsInput.val();
        applyLocalSettings();
    })

    
});



