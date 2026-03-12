const websocketUrl = "ws://localhost:9001/";
const backgroundCheckPeriodMs = 500;

const { createApp } = Vue;

const app = createApp({
    components: {},
    data() {
        return {
            bridges: {
                versions: [],
                selected: "",
                outputToLogfile: false,
                status: "unknown",
                statusColor: "black",
                hasSuiteLocal: false,
            },
            tropic: {
                outputToLogfile: true,
                status: "unknown",
                statusColor: "black",
            },
            emulators: {
                versions: {
                    T1B1: {
                        header: "Trezor One",
                        versions: [],
                    },
                    T2T1: {
                        header: "Trezor T",
                        versions: [],
                    },
                    T3B1: {
                        header: "Trezor Safe 3",
                        versions: [],
                    },
                    T3T1: {
                        header: "Trezor Safe 5",
                        versions: [],
                    },
                    T3W1: {
                        header: "Trezor Safe 7",
                        versions: [],
                    },
                },
                wipeDevice: false,
                screenshotMode: false,
                animations: false,
                outputToLogfile: false,
                status: "unknown",
                statusColor: "black",
            },
            emulatorUrl: {
                url: "",
                model: "",
            },
            emulatorBranch: {
                branch: "",
                model: "",
                btcOnly: false,
            },
            emulatorDownloadMessage: "",
            emulatorCommands: {
                seed: "",
                shamirShares: 3,
                shamirThreshold: 2,
            },
            server: {
                command: '{"type": "specify"}',
            },
            regtest: {
                status: "unknown",
                statusColor: "black",
                mineBlocks: 1,
                mineAddress: "",
                sendAmount: 10,
                sendAddress: "",
            },
            ws: null,
            isWaitingForResponse: false,
            enablePassphrase: true,
            req_id: 0,
            logs: [],
            notifications: {
                showPopup: false,
                text: "",
                header: "Notification",
                isError: false,
            },
            emulatorWasRunning: false,
            emulatorPopoutTimer: null,
            emulatorPopoutWindow: null,
            emulatorLastStatus: null,
        };
    },
    created() {
        this.setupWebSocket();
        setInterval(this.getBackgroundStatus, backgroundCheckPeriodMs);
    },
    mounted() {
        this.$nextTick(() => {
            document.getElementById("app").style.display = "block";
        });
        // listen for Esc key and close the notification
        window.addEventListener("keydown", (event) => {
            if (this.notifications.showPopup && event.key === "Escape") {
                this.notifications.showPopup = false;
            }
        });
    },
    computed: {
        vncUrl() {
            // Use custom trezor.html for a perfectly integrated UI
            const host = window.location.hostname;
            return `http://${host}:6080/trezor.html?autoconnect=1`;
        },
    },
    watch: {
        'emulatorUrl.url': function (newUrl) {
            this.updateModelFromUrl(newUrl);
        }
    },
    methods: {
        updateModelFromUrl(url) {
            Object.keys(this.emulators.versions).forEach((model) => {
                if (url.toLowerCase().includes(model.toLowerCase())) {
                    this.emulatorUrl.model = model;
                }
            });
        },
        setupWebSocket() {
            this.ws = new WebSocket(websocketUrl);

            this.ws.onmessage = this.handleMessage;

            this.ws.onerror = (event) => {
                this.logEvent(
                    `WebSocket connection Error. Event: ${JSON.stringify(
                        event
                    )}`,
                    "red"
                );
                this.showNotification("WebSocket error", true);
            };

            this.ws.onclose = (event) => {
                this.logEvent(
                    `WebSocket connection closed. Event: ${JSON.stringify(
                        event
                    )}`,
                    "red"
                );
                this.ws = null;
            };

            this.ws.onopen = () => {
                this.logEvent("WebSocket connection opened", "green");
            };
        },
        handleMessage(event) {
            try {
                JSON.parse(event.data);
            } catch (err) {
                this.logEvent(
                    `Response received is not a valid JSON: ${event.data}`,
                    "red"
                );
                return;
            }

            this.isWaitingForResponse = false;

            const dataObject = JSON.parse(event.data);

            if (
                "background_check" in dataObject &&
                dataObject.background_check
            ) {
                this.reflectBackgroundSituationInGUI(dataObject);
                return;
            }

            let color = "black";
            if ("success" in dataObject) {
                if (dataObject.success) {
                    color = "green";
                } else {
                    color = "red";
                    this.showNotification(
                        "Some error happened, please look into Log below.",
                        true
                    );
                    this.emulatorDownloadMessage = "";
                }
            }

            if (
                "response" in dataObject &&
                typeof dataObject.response === 'string' &&
                dataObject.response.includes("Emulator downloaded")
            ) {
                this.emulatorDownloadMessage = "";
            }

            this.logEvent(`Response received: ${event.data}`, color);

            // Filling the possible options for the emulators/bridges
            if (dataObject.type === "client") {
                for (const model in dataObject.firmwares) {
                    const options = dataObject.firmwares[model];
                    this.emulators.versions[model].versions = options;
                    this.emulators.versions[model].selected = options[0];
                }
                const nodebridge = [];
                const legacy = [];
                dataObject.bridges.forEach((b) =>
                    b.startsWith("2.") ? legacy.push(b) : nodebridge.push(b)
                );
                this.bridges.versions = nodebridge.concat(legacy);
                this.bridges.selected = this.bridges.versions[0];

                this.bridges.hasSuiteLocal = dataObject.bridges.includes(
                    "local-suite-node-bridge"
                );
            }
        },
        sendMessage(msg) {
            if (this.isWaitingForResponse) {
                this.logEvent("Waiting for response, please wait...", "red");
                return;
            }

            if (!msg) {
                this.showNotification("Please enter a message", true);
                return;
            }
            if (!this.ws) {
                this.logEvent("WebSocket not connected", "red");
                this.showNotification(
                    "WebSocket not connected - trying to connect...",
                    true
                );
                this.setupWebSocket();
                this.sendMessage(msg);
                return;
            }

            this.logEvent(`Request sent: ${JSON.stringify(msg)}`, "blue");

            const requestToSend = JSON.stringify(
                Object.assign(msg, {
                    id: this.req_id,
                })
            );
            this.ws.send(requestToSend);
            this.req_id++;

            this.isWaitingForResponse = true;
        },
        sendMessageOnBackground(json) {
            if (!this.ws) {
                return;
            }
            this.ws.send(JSON.stringify(json));
        },
        getBackgroundStatus() {
            this.sendMessageOnBackground({
                type: "background-check",
            });
        },
        showNotification(text, isError = false) {
            this.notifications.text = text;
            this.notifications.showPopup = true;
            this.notifications.isError = isError;
            this.notifications.header = isError ? "Error" : "Notification";
        },
        bridgeStart() {
            this.sendMessage({
                type: "bridge-start",
                version: this.bridges.selected,
                output_to_logfile: this.bridges.outputToLogfile,
            });
        },
        bridgeStop() {
            this.sendMessage({
                type: "bridge-stop",
            });
        },
        tropicStart() {
            this.sendMessage({
                type: "tropic-start",
                output_to_logfile: this.tropic.outputToLogfile,
            });
        },
        tropicStop() {
            this.sendMessage({
                type: "tropic-stop",
            });
        },
        emulatorStart(model) {
            const emulator = this.emulators.versions[model];
            if (!emulator) {
                this.showNotification("No emulator selected", true);
                return;
            }
            if (!emulator.selected) {
                this.showNotification("Please select a version first", true);
                return;
            }

            this.sendMessage({
                type: "emulator-start",
                version: emulator.selected,
                model,
                wipe: this.emulators.wipeDevice,
                output_to_logfile: this.emulators.outputToLogfile,
                save_screenshots: this.emulators.screenshotMode,
                show_animations: this.emulators.animations,
            });
        },
        emulatorStartFromUrl() {
            const url = this.emulatorUrl.url;
            if (!url) {
                this.showNotification("URL is empty!", true);
                return;
            }

            const model = this.emulatorUrl.model;
            if (!model) {
                this.showNotification("Model is empty!", true);
                return;
            }

            this.sendMessage({
                type: "emulator-start-from-url",
                url,
                model,
                wipe: this.emulators.wipeDevice,
                output_to_logfile: this.emulators.outputToLogfile,
                save_screenshots: this.emulators.screenshotMode,
                show_animations: this.emulators.animations,
            });

            this.emulatorDownloadMessage =
                "Emulator started downloading, it may take a while...";
        },
        emulatorStartFromBranch() {
            let branch = this.emulatorBranch.branch;
            if (!branch) {
                this.showNotification("Branch is empty!", true);
                return;
            }

            const model = this.emulatorBranch.model;
            if (!model) {
                this.showNotification("Model is empty!", true);
                return;
            }

            this.sendMessage({
                type: "emulator-start-from-branch",
                branch,
                model,
                btc_only: this.emulatorBranch.btcOnly,
                wipe: this.emulators.wipeDevice,
                output_to_logfile: this.emulators.outputToLogfile,
                save_screenshots: this.emulators.screenshotMode,
                show_animations: this.emulators.animations,
            });

            this.emulatorDownloadMessage =
                "Emulator started downloading, it may take a while...";
        },
        reflectBackgroundSituationInGUI(dataObject) {
            if ("bridge_status" in dataObject) {
                this.reflectBridgeSituation(dataObject.bridge_status);
            }
            if ("emulator_status" in dataObject) {
                this.reflectEmulatorSituation(dataObject.emulator_status);
            }
            if ("tropic_status" in dataObject) {
                this.reflectTropicSituation(dataObject.tropic_status);
            }
            if ("regtest_status" in dataObject) {
                this.reflectRegtestSituation(dataObject.regtest_status);
            }
        },
        reflectBridgeSituation(status) {
            if (status.is_running) {
                // Can happen that bridge is already running on the background, but
                //   was not spawned by the GUI (causing confusion)
                if (!status.version) {
                    this.showNotification(
                        "It seems you already have an instance of bridge running - please kill it. `ps -ef | grep trezor` ... `kill <pid>`",
                        true
                    );
                }
                this.writeBridgeStatus(`Running - ${status.version}`, "green");
            } else {
                this.writeBridgeStatus("Stopped", "red");
            }
        },
        reflectEmulatorSituation(status) {
            const startedNow = status.is_running && !this.emulatorWasRunning;
            this.emulatorLastStatus = status;

            if (status.is_running) {
                this.writeEmulatorStatus(
                    `Running - ${status.version}`,
                    "green"
                );
            } else {
                this.writeEmulatorStatus("Stopped", "red");
            }

            if (startedNow) {
                this.scheduleVncPopout(status);
            }

            if (!status.is_running) {
                this.closeVncPopout();
            }

            this.emulatorWasRunning = status.is_running;
        },
        scheduleVncPopout(status) {
            if (this.emulatorPopoutTimer) {
                clearTimeout(this.emulatorPopoutTimer);
            }

            this.emulatorPopoutTimer = window.setTimeout(() => {
                this.openVncPopout(status);
                this.emulatorPopoutTimer = null;
            }, 1000);
        },
        getFallbackViewport(model) {
            const dimensions = {
                T1B1: { width: 256, height: 128 },
                T2T1: { width: 240, height: 240 },
                T3B1: { width: 128, height: 64 },
                T3T1: { width: 240, height: 240 },
                T3W1: { width: 240, height: 320 },
            };
            return dimensions[model] || { width: 800, height: 800 };
        },
        getEmulatorViewport(status) {
            const windowSize = status && status.window_size;
            if (windowSize && windowSize.width && windowSize.height) {
                return {
                    width: windowSize.width,
                    height: windowSize.height,
                };
            }

            return this.getFallbackViewport(status && status.model);
        },
        resizePopoutViewport(popout, viewport) {
            try {
                const chromeWidth = Math.max(popout.outerWidth - popout.innerWidth, 0);
                const chromeHeight = Math.max(popout.outerHeight - popout.innerHeight, 0);

                popout.resizeTo(
                    Math.max(viewport.width + chromeWidth, 200),
                    Math.max(viewport.height + chromeHeight, 200)
                );
            } catch (_err) {
                // Browser may block resize in some environments.
            }
        },
        closeVncPopout() {
            if (this.emulatorPopoutTimer) {
                clearTimeout(this.emulatorPopoutTimer);
                this.emulatorPopoutTimer = null;
            }

            if (this.emulatorPopoutWindow && !this.emulatorPopoutWindow.closed) {
                this.emulatorPopoutWindow.close();
            }
            this.emulatorPopoutWindow = null;
        },
        reflectTropicSituation(status) {
            if (status.is_running) {
                this.writeTropicStatus(`Running - ${status.version}`, "green");
            } else {
                this.writeTropicStatus("Stopped", "red");
            }
        },
        reflectRegtestSituation(is_running) {
            if (is_running) {
                this.writeRegtestStatus("Running", "green");
            } else {
                this.writeRegtestStatus("Stopped", "red");
            }
        },
        writeBridgeStatus(status, color = "black") {
            this.bridges.status = status;
            this.bridges.statusColor = color;
        },
        writeEmulatorStatus(status, color = "black") {
            this.emulators.status = status;
            this.emulators.statusColor = color;
        },
        writeTropicStatus(status, color = "black") {
            this.tropic.status = status;
            this.tropic.statusColor = color;
        },
        writeRegtestStatus(status, color = "black") {
            this.regtest.status = status;
            this.regtest.statusColor = color;
        },
        sendServerCommand() {
            // Defending against invalid JSON
            const command = this.server.command;
            try {
                JSON.parse(command);
            } catch (err) {
                this.showNotification("Invalid JSON provided!", true);
                return;
            }

            this.logEvent(`Sent manually: ${command}`, "magenta");
            this.sendMessage(JSON.parse(command));
            this.$nextTick(() => {
                document.getElementById("server-input").focus();
            });
        },
        closeWebsocket() {
            this.ws.close();
        },
        exit() {
            this.sendMessage({
                type: "exit",
            });
        },
        ping() {
            this.sendMessage({
                type: "ping",
            });
        },
        emulatorWipe() {
            this.sendMessage({
                type: "emulator-wipe",
            });
        },
        emulatorResetDevice() {
            this.sendMessage({
                type: "emulator-reset-device",
            });
        },
        emulatorResetDeviceShamir() {
            this.sendMessage({
                type: "emulator-reset-device",
                use_shamir: true,
            });
        },
        emulatorSetup(seedName = "") {
            const mapping = {
                all: "all all all all all all all all all all all all",
                academic:
                    "academic again academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic pecan provide remember",
            };

            const seed = mapping[seedName] || this.emulatorCommands.seed;
            if (!seed) {
                this.showNotification("Please enter a seed", true);
                return;
            }
            this.sendMessage({
                type: "emulator-setup",
                mnemonic: seed,
                pin: "",
                passphrase_protection: this.enablePassphrase,
                label: "Hello!",
            });
        },
        emulatorPressYes() {
            this.sendMessage({
                type: "emulator-press-yes",
            });
        },
        emulatorPressNo() {
            this.sendMessage({
                type: "emulator-press-no",
            });
        },
        emulatorAllowUnsafe() {
            this.sendMessage({
                type: "emulator-allow-unsafe-paths",
            });
        },
        emulatorStop() {
            this.sendMessage({
                type: "emulator-stop",
            });
        },
        readAndConfirmMnemonic() {
            this.sendMessage({
                type: "emulator-read-and-confirm-mnemonic",
            });
        },
        readAndConfirmMnemonicShamir() {
            this.sendMessage({
                type: "emulator-read-and-confirm-shamir-mnemonic",
                shares: this.emulatorCommands.shamirShares,
                threshold: this.emulatorCommands.shamirThreshold,
            });
        },
        emulatorSetBackupState() {
            this.sendMessage({
                type: "emulator-set-for-backup",
            });
        },
        emulatorGetFeatures() {
            this.sendMessage({
                type: "emulator-get-features",
            });
        },
        regtestMine() {
            this.sendMessage({
                type: "regtest-mine-blocks",
                block_amount: this.regtest.mineBlocks,
                address: this.regtest.mineAddress,
            });
        },
        regtestSend() {
            this.sendMessage({
                type: "regtest-send-to-address",
                btc_amount: this.regtest.sendAmount,
                address: this.regtest.sendAddress,
            });
        },
        openVncPopout(status = this.emulatorLastStatus) {
            try {
                const viewport = this.getEmulatorViewport(status || {});

                if (this.emulatorPopoutWindow && !this.emulatorPopoutWindow.closed) {
                    this.emulatorPopoutWindow.focus();
                    this.resizePopoutViewport(this.emulatorPopoutWindow, viewport);
                    return;
                }

                const width = viewport.width;
                const height = viewport.height;
                const left = (window.screen.width / 2) - (width / 2);
                const top = (window.screen.height / 2) - (height / 2);
                const popout = window.open(
                    "about:blank",
                    "TrezorEmulatorDisplay",
                    `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=no`
                );
                if (!popout || popout.closed || typeof popout.closed == 'undefined') {
                    this.showNotification("Pop-up was blocked by your browser. Please allow pop-ups for this site.", true);
                    return;
                }

                this.emulatorPopoutWindow = popout;
                this.resizePopoutViewport(popout, viewport);
                const vncUrl = this.vncUrl;

                popout.document.open();
                popout.document.write(`<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Trezor Emulator Display</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background: #000;
            overflow: hidden;
            font-family: sans-serif;
        }
        #status {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 16px;
            background: #000;
            z-index: 1;
        }
        #frame {
            width: 100%;
            height: 100%;
            border: none;
            display: none;
            background: #000;
        }
    </style>
</head>
<body>
    <div id="status">Waiting for emulator display...</div>
    <iframe id="frame" allow="fullscreen" tabindex="-1"></iframe>
    <script>
        const targetUrl = ${JSON.stringify(vncUrl)};
        const status = document.getElementById('status');
        const frame = document.getElementById('frame');
        const maxAttempts = 60;
        let attempts = 0;
        let frameLoaded = false;
        const targetOrigin = (() => {
            try {
                return new URL(targetUrl).origin;
            } catch (_err) {
                return '*';
            }
        })();

        const sendFocusRequest = () => {
            try {
                if (frame.contentWindow) {
                    frame.contentWindow.postMessage({ type: 'trezor-focus-emulator' }, targetOrigin);
                }
            } catch (_err) {
                // Cross-origin access is expected; postMessage is best-effort.
            }
        };

        const focusEmulatorFrame = () => {
            try {
                frame.focus();
                if (frame.contentWindow) {
                    frame.contentWindow.focus();
                }
            } catch (_error) {
                frame.focus();
            }
            sendFocusRequest();
        };

        frame.addEventListener('load', () => {
            frameLoaded = true;
            frame.style.display = 'block';
            status.style.display = 'none';
            setTimeout(focusEmulatorFrame, 0);
            setTimeout(sendFocusRequest, 120);
            setTimeout(sendFocusRequest, 300);
        });

        window.addEventListener('focus', () => {
            setTimeout(focusEmulatorFrame, 0);
        });

        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                setTimeout(focusEmulatorFrame, 0);
            }
        });

        const tryConnect = async () => {
            if (frameLoaded) {
                return;
            }

            attempts += 1;
            try {
                await fetch(targetUrl, { mode: 'no-cors', cache: 'no-store' });
                if (!frame.src) {
                    frame.src = targetUrl;
                }
                return;
            } catch (error) {
                if (attempts >= maxAttempts) {
                    status.textContent = 'Emulator display is not reachable.';
                    return;
                }
            }

            setTimeout(tryConnect, 500);
        };

        tryConnect();
    <\/script>
</body>
</html>`);
                popout.document.close();
            } catch (err) {
                this.logEvent(`Pop-out error: ${err.message}`, "red");
                this.showNotification(`Failed to open pop-out: ${err.message}`, true);
            }
        },
        logEvent(text, color = "black") {
            const newLog = {
                text: `${currentTime()} - ${text}`,
                color,
            };
            this.logs.unshift(newLog);
        },
    },
});

app.mount("#app");

const currentTime = () => {
    const now = new Date();
    const hours = ("0" + now.getHours()).slice(-2);
    const minutes = ("0" + now.getMinutes()).slice(-2);
    const seconds = ("0" + now.getSeconds()).slice(-2);
    return `${hours}:${minutes}:${seconds}`;
};
