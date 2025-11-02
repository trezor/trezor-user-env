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
                this.bridges.selected = dataObject.bridges[0];
                this.bridges.versions = dataObject.bridges;
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
            if (status.is_running) {
                this.writeEmulatorStatus(
                    `Running - ${status.version}`,
                    "green"
                );
            } else {
                this.writeEmulatorStatus("Stopped", "red");
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
