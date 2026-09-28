const websocketUrl = "ws://localhost:9001/";
const backgroundCheckPeriodMs = 500;
const WS_MAX_RETRIES = 4;

// Safe localStorage wrapper — file:// in some browsers throws SecurityError.
const store = {
    get: function(key, fallback) {
        try { return localStorage.getItem(key) || (fallback !== undefined ? fallback : null); }
        catch (e) { return fallback !== undefined ? fallback : null; }
    },
    set: function(key, value) {
        try { localStorage.setItem(key, value); } catch (e) { /* ignore */ }
    },
};

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
                runningVersion: null,
                autoStart: store.get('userEnvBridgeAutoStart') === 'true',
            },
            tropic: {
                outputToLogfile: true,
                status: "unknown",
                statusColor: "black",
                runningVersion: null,
            },
            selectedEmulatorModel: store.get('userEnvSelectedModel', 'T3W1'),
            emulators: {
                versions: {
                    T1B1: {
                        header: "Trezor One",
                        inputType: "Buttons",
                        versions: [],
                    },
                    T2T1: {
                        header: "Trezor T",
                        inputType: "Touch",
                        versions: [],
                    },
                    T3B1: {
                        header: "Trezor Safe 3",
                        inputType: "Buttons",
                        versions: [],
                    },
                    T3T1: {
                        header: "Trezor Safe 5",
                        inputType: "Touch",
                        versions: [],
                    },
                    T3W1: {
                        header: "Trezor Safe 7",
                        inputType: "Touch",
                        versions: [],
                    },
                },
                runningModel: null,
                runningVersion: null,
                wipeDevice: false,
                screenshotMode: false,
                animations: false,
                outputToLogfile: false,
                vncActive: false,
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
            customFirmwareSource: "url",
            customFirmwareOpen: false,
            bootloaderMockOpen: false,
            bootloaderMock: {
                model: "T3W1",
            },
            suiteMountOpen: false,
            emulatorCommands: {
                seed: "",
                shamirShares: 3,
                shamirThreshold: 2,
                n4w1TagId: 1,
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
            openFly: null,
            logExpanded: false,
            logSide: store.get('userEnvLogSide') === 'true',
            logSideWidth: parseInt(store.get('userEnvLogSideWidth', '420'), 10),
            logBottomHeight: parseInt(store.get('userEnvLogBottomHeight', '240'), 10),
            logFilters: new Set(
                (store.get('userEnvLogFilters', 'out,ok,err,raw,sys')).split(',').filter(Boolean)
            ),
            logFilterOpen: false,
            theme: store.get('userEnvTheme', 'dark'),
            copyFlash: null,
            vncCacheBuster: Date.now(),
            unseenLogs: 0,
            wsReconnecting: false,
            wsRetries: 0,
            wsRetryTimer: null,
        };
    },
    created() {
        // Guard against stale / hand-edited localStorage values that would
        // blow up templates like emulators.versions[selectedEmulatorModel].
        if (!Object.prototype.hasOwnProperty.call(this.emulators.versions, this.selectedEmulatorModel)) {
            this.selectedEmulatorModel = 'T3W1';
        }
        this.setupWebSocket();
        setInterval(this.getBackgroundStatus, backgroundCheckPeriodMs);
    },
    mounted() {
        document.documentElement.setAttribute('data-theme', this.theme);
        this.$nextTick(() => {
            document.getElementById("app").style.display = "block";
        });
        document.documentElement.style.setProperty('--log-side-width', this.logSideWidth + 'px');
        document.documentElement.style.setProperty('--log-bottom-height', this.logBottomHeight + 'px');
        // Close filter dropdown on outside click.
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.log-filter-dropdown')) this.logFilterOpen = false;
        });
        // Esc: close popup first, then any open flyout.
        window.addEventListener("keydown", (event) => {
            if (event.key !== "Escape") return;
            if (this.notifications.showPopup) {
                this.notifications.showPopup = false;
            } else if (this.openFly) {
                this.openFly = null;
            }
        });
    },
    computed: {
        bridgeStatusClass() {
            if (this.bridges.statusColor === 'green') return 'status-pill--ok';
            if (this.bridges.statusColor === 'red') return 'status-pill--error';
            return 'status-pill--unknown';
        },
        emulatorStatusClass() {
            if (this.emulators.statusColor === 'green') return 'status-pill--ok';
            if (this.emulators.statusColor === 'red') return 'status-pill--error';
            return 'status-pill--unknown';
        },
        tropicStatusClass() {
            if (this.tropic.statusColor === 'green') return 'status-pill--ok';
            if (this.tropic.statusColor === 'red') return 'status-pill--error';
            return 'status-pill--unknown';
        },
        regtestStatusClass() {
            if (this.regtest.statusColor === 'green') return 'status-pill--ok';
            if (this.regtest.statusColor === 'red') return 'status-pill--error';
            return 'status-pill--unknown';
        },
        vncUrl() {
            const bg = this.theme === 'dark' ? '#14171a' : '#f4f5f7';
            return `http://localhost:6080/vnc_embed.html?background=${encodeURIComponent(bg)}&t=${this.vncCacheBuster}`;
        },
        showTropicSection() {
            // Section §5: shown when T3W1 is selected or currently running.
            return this.selectedEmulatorModel === 'T3W1' ||
                   this.emulators.runningModel === 'T3W1';
        },
        emulatorHasButtons() {
            const model = this.emulators.runningModel || this.selectedEmulatorModel;
            return this.emulators.versions[model]?.inputType === 'Buttons';
        },
        modernBridgeVersions() {
            // Spec §3: node-bridge (modern) group — anything not starting with "2."
            return this.bridges.versions.filter(v => !v.startsWith('2.'));
        },
        legacyBridgeVersions() {
            // Spec §3: legacy 2.x group.
            return this.bridges.versions.filter(v => v.startsWith('2.'));
        },
        filteredLogs() {
            return this.logs.filter(l => this.logFilters.has(l.kind));
        },
        logFiltersActive() {
            return this.logFilters.size < 5;
        },
        logFilterOptions() {
            return [
                { k: 'out', label: 'Out',    tip: 'Outbound requests sent to the backend' },
                { k: 'ok',  label: 'Ok',     tip: 'Successful responses from the backend' },
                { k: 'err', label: 'Err',    tip: 'Error responses and failures' },
                { k: 'raw', label: 'Raw',    tip: 'Raw WebSocket messages (sent manually)' },
                { k: 'sys', label: 'System', tip: 'Internal events: connect, disconnect, retry' },
            ];
        },
    },
    watch: {
        'emulatorUrl.url': function (newUrl) {
            this.updateModelFromUrl(newUrl);
        },
        selectedEmulatorModel(v) {
            if (v) store.set('userEnvSelectedModel', v);
        },
        'bridges.autoStart'(v) {
            store.set('userEnvBridgeAutoStart', v ? 'true' : 'false');
        },
        logSide(v) {
            store.set('userEnvLogSide', v ? 'true' : 'false');
        },
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
            // Clear any pending auto-retry that might fire while we're already connecting.
            if (this.wsRetryTimer) {
                clearTimeout(this.wsRetryTimer);
                this.wsRetryTimer = null;
            }

            this.ws = new WebSocket(websocketUrl);

            this.ws.onmessage = this.handleMessage;

            this.ws.onerror = (event) => {
                this.logEvent(
                    `WebSocket connection Error. Event: ${JSON.stringify(
                        event
                    )}`,
                    "var(--red)"
                );
                // Deliberately no blocking notification here — auto-retry will handle it
                // and the user already sees the log entry + sidebar reconnect button.
            };

            this.ws.onclose = (event) => {
                this.logEvent(
                    `WebSocket connection closed. Event: ${JSON.stringify(
                        event
                    )}`,
                    "var(--red)"
                );
                this.ws = null;
                // Exponential backoff auto-retry, up to WS_MAX_RETRIES.
                if (this.wsRetries < WS_MAX_RETRIES) {
                    const delayMs = [1000, 2000, 5000, 10000][this.wsRetries] || 10000;
                    this.wsRetries++;
                    this.wsReconnecting = true;
                    this.logEvent(
                        `Reconnecting in ${Math.round(delayMs/1000)}s (attempt ${this.wsRetries}/${WS_MAX_RETRIES})…`,
                        "var(--amber)"
                    );
                    this.wsRetryTimer = setTimeout(() => this.setupWebSocket(), delayMs);
                } else {
                    this.wsReconnecting = false;
                }
            };

            this.ws.onopen = () => {
                this.logEvent("WebSocket connection opened", "var(--primary)");
                this.wsRetries = 0;
                this.wsReconnecting = false;
            };
        },
        handleMessage(event) {
            try {
                JSON.parse(event.data);
            } catch (err) {
                this.logEvent(
                    `Response received is not a valid JSON: ${event.data}`,
                    "var(--red)"
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

            let color;
            if ("success" in dataObject) {
                if (dataObject.success) {
                    color = "var(--primary)";
                } else {
                    color = "var(--red)";
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

            // Show inline VNC viewer when emulator starts
            if (dataObject.emulator_started) {
                this.emulators.vncActive = true;
                this.$nextTick(() => this.reloadVnc());
            }

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

                // Wait one background-check tick so `bridges.statusColor`
                // reflects the live state; then decide whether to auto-start.
                setTimeout(() => this.maybeAutoStartBridge(), backgroundCheckPeriodMs + 100);
            }
        },
        sendMessage(msg) {
            if (this.isWaitingForResponse) {
                this.logEvent("Waiting for response, please wait...", "var(--red)");
                return;
            }

            if (!msg) {
                this.showNotification("Please enter a message", true);
                return;
            }
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this.logEvent("WebSocket not connected", "var(--red)");
                this.showNotification(
                    "WebSocket not connected – trying to connect…",
                    true
                );
                if (!this.ws) this.setupWebSocket();
                return;
            }

            this.logEvent(`Request sent: ${JSON.stringify(msg)}`, "var(--blue)");

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
            // Skip if the socket isn't OPEN — sending on CONNECTING or CLOSING
            // throws InvalidStateError and would drop the background-check.
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                return;
            }
            this.ws.send(JSON.stringify(json));
        },
        getBackgroundStatus() {
            this.sendMessageOnBackground({
                type: "background-check",
            });
        },
        showNotification(text, isError = true) {
            // The error modal is only used for backend failures / validation blockers.
            // `isError` is kept in the signature for backwards compatibility.
            this.notifications.text = text;
            this.notifications.showPopup = true;
            this.notifications.isError = isError;
            this.notifications.header = "Error";
        },
        bridgeStart() {
            // Remember the version so the dashboard can auto-start it on the
            // next load when the user has opted in (see `userEnvBridgeAutoStart`).
            store.set('userEnvLastBridge', this.bridges.selected);
            this.sendMessage({
                type: "bridge-start",
                version: this.bridges.selected,
                output_to_logfile: this.bridges.outputToLogfile,
            });
        },
        bridgeStop() {
            // Explicit stop clears the remembered version so a subsequent
            // load doesn't bring back what the user just shut down.
            store.set('userEnvLastBridge', '');
            this.sendMessage({
                type: "bridge-stop",
            });
        },
        maybeAutoStartBridge() {
            // Only fire once, after the `client` message delivers the live
            // version list AND background-check has told us the bridge is
            // not already running.
            if (!this.bridges.autoStart) return;
            const last = store.get('userEnvLastBridge');
            if (!last) return;
            if (!this.bridges.versions.includes(last)) return;
            if (this.bridges.statusColor === 'green') return;
            this.bridges.selected = last;
            this.bridgeStart();
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
            // If the flyout is open, close it so the user sees the device stage come to life.
            if (this.openFly === 'flyEmu') this.closeFlyouts();
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
            // Close the flyout so the user can see the download progress + device stage.
            this.closeFlyouts();
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
            this.closeFlyouts();
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
                this.bridges.runningVersion = status.version || null;
            } else {
                this.writeBridgeStatus("Stopped", "red");
                this.bridges.runningVersion = null;
            }
        },
        reflectEmulatorSituation(status) {
            if (status.is_running) {
                this.writeEmulatorStatus(
                    `Running - ${status.version}`,
                    "green"  // statusColor — used for CSS class, not inline style
                );
                const match = status.version && status.version.match(/\((\w+)\)$/);
                this.emulators.runningModel = match ? match[1] : null;
                this.emulators.runningVersion = status.version
                    ? status.version.replace(/\s*\(\w+\)$/, "")
                    : null;
                if (!this.emulators.vncActive) {
                    this.emulators.vncActive = true;
                    this.$nextTick(() => this.reloadVnc());
                }
            } else {
                this.writeEmulatorStatus("Stopped", "red");
                this.emulators.vncActive = false;
                this.emulators.runningModel = null;
                this.emulators.runningVersion = null;
            }
        },
        reflectTropicSituation(status) {
            if (status.is_running) {
                this.writeTropicStatus(`Running - ${status.version}`, "green");
                this.tropic.runningVersion = status.version || null;
            } else {
                this.writeTropicStatus("Stopped", "red");
                this.tropic.runningVersion = null;
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

            this.logEvent(`Sent manually: ${command}`, "var(--amber)");
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
        emulatorExperimentalFeatures() {
            this.sendMessage({
                type: "emulator-apply-settings",
                experimental_features: true,
            });
        },
        reloadVnc() {
            this.vncCacheBuster = Date.now();
        },
        openVncPopup() {
            const w = 350;
            const h = 666;
            const availW = (window.screen && window.screen.availWidth)  || window.innerWidth;
            const availH = (window.screen && window.screen.availHeight) || window.innerHeight;
            const left = Math.max(0, (availW - w) / 2);
            const top  = Math.max(0, (availH - h) / 2);
            const popup = window.open("about:blank", "novnc-viewer", `popup=yes,width=${w},height=${h},left=${left},top=${top}`);
            if (popup) {
                popup.location.href = this.vncUrl;
            } else {
                this.showNotification("Popup blocked. Allow popups for this site to open the emulator in a separate window.", true);
            }
        },
        emulatorStop() {
            this.emulators.vncActive = false;
            this.sendMessage({
                type: "emulator-stop",
            });
        },
        emulatorStartBootloaderMock() {
            const model = this.bootloaderMock.model;
            if (!model) {
                this.showNotification("Pick a model for the bootloader mock!", true);
                return;
            }
            // The mock has no display; hide the VNC viewer if it was showing.
            this.emulators.vncActive = false;
            this.sendMessage({
                type: "emulator-start-bootloader",
                model,
            });
            this.closeFlyouts();
        },
        readAndConfirmMnemonic() {
            this.sendMessage({
                type: "emulator-read-and-confirm-mnemonic",
            });
        },
        readAndConfirmSingleShamirMnemonic() {
            this.sendMessage({
                type: "emulator-read-and-confirm-single-shamir-mnemonic",
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
        n4w1Tap() {
            this.sendMessage({
                type: "emulator-n4w1-tap",
                tag_id: this.emulatorCommands.n4w1TagId.toString(),
            });
        },
        n4w1Clear() {
            this.sendMessage({
                type: "emulator-n4w1-clear",
                tag_id: this.emulatorCommands.n4w1TagId.toString(),
            });
        },
        emulatorGetFeatures() {
            this.sendMessage({
                type: "emulator-get-features",
            });
        },
        regtestMine() {
            const blocks = Number(this.regtest.mineBlocks);
            if (!blocks || blocks < 1 || blocks > 10000) {
                this.showNotification("Block count must be between 1 and 10 000.", true);
                return;
            }
            // Address is optional — the backend falls back to getnewaddress()
            // when it's omitted. Only trim + send if the user provided one.
            const payload = { type: "regtest-mine-blocks", block_amount: blocks };
            const addr = (this.regtest.mineAddress || "").trim();
            if (addr) payload.address = addr;
            this.sendMessage(payload);
        },
        regtestSend() {
            const amount = Number(this.regtest.sendAmount);
            if (!amount || amount <= 0) {
                this.showNotification("BTC amount must be greater than 0.", true);
                return;
            }
            if (!this.regtest.sendAddress || !this.regtest.sendAddress.trim()) {
                this.showNotification("Enter a destination address.", true);
                return;
            }
            this.sendMessage({
                type: "regtest-send-to-address",
                btc_amount: amount,
                address: this.regtest.sendAddress.trim(),
            });
        },
        logKind(text, color) {
            if (text.indexOf('Request sent') === 0) return 'out';
            if (text.indexOf('Sent manually') === 0) return 'raw';
            if (text.indexOf('Response received') === 0) {
                if (color && color.indexOf('--red') !== -1) return 'err';
                return 'ok';
            }
            if (text.indexOf('connection opened') !== -1) return 'ok';
            if (color && color.indexOf('--red') !== -1) return 'err';
            return 'sys';
        },
        logEvent(text, color) {
            const kind = this.logKind(text, color);
            const newLog = {
                id: this.req_id + '_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7),
                text: `${currentTime()} - ${text}`,
                color,
                kind,
            };
            // Track whether the user was already near the top before we prepend.
            const el = this.$refs.logContainer;
            const nearTop = !el || el.scrollTop < 60;
            this.logs.unshift(newLog);
            // Cap log length so the DOM stays light for long sessions.
            if (this.logs.length > 500) this.logs.length = 500;
            // Auto-scroll only if the user was already near the top.
            if (nearTop) {
                this.$nextTick(() => { if (el) el.scrollTop = 0; });
            } else {
                this.unseenLogs = (this.unseenLogs || 0) + 1;
            }
        },
        startLogBottomResize(e) {
            e.preventDefault();
            const handle = e.currentTarget;
            const startY = e.clientY;
            const startHeight = this.logBottomHeight;
            handle.classList.add('dragging');
            document.body.style.cursor = 'row-resize';
            document.body.style.pointerEvents = 'none';
            handle.style.pointerEvents = 'auto';
            const onMove = (ev) => {
                const h = Math.max(100, Math.min(startHeight - (ev.clientY - startY), window.innerHeight - 300));
                this.logBottomHeight = h;
                document.documentElement.style.setProperty('--log-bottom-height', h + 'px');
            };
            const onUp = () => {
                handle.classList.remove('dragging');
                document.body.style.cursor = '';
                document.body.style.pointerEvents = '';
                handle.style.pointerEvents = '';
                store.set('userEnvLogBottomHeight', String(this.logBottomHeight));
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
            };
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        },
        startLogResize(e) {
            e.preventDefault();
            const handle = e.currentTarget;
            const startX = e.clientX;
            const startWidth = this.logSideWidth;
            handle.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            document.body.style.pointerEvents = 'none';
            handle.style.pointerEvents = 'auto';
            const onMove = (ev) => {
                const w = Math.max(390, Math.min(startWidth + ev.clientX - startX, 1150));
                this.logSideWidth = w;
                document.documentElement.style.setProperty('--log-side-width', w + 'px');
            };
            const onUp = () => {
                handle.classList.remove('dragging');
                document.body.style.cursor = '';
                document.body.style.pointerEvents = '';
                handle.style.pointerEvents = '';
                store.set('userEnvLogSideWidth', String(this.logSideWidth));
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
            };
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        },
        toggleFilter(k) {
            const f = new Set(this.logFilters);
            if (f.has(k)) { f.delete(k); } else { f.add(k); }
            this.logFilters = f;
            store.set('userEnvLogFilters', [...f].join(','));
        },
        clearUnseen() {
            this.unseenLogs = 0;
            const el = this.$refs.logContainer;
            if (el) el.scrollTop = 0;
        },
        onLogScroll() {
            const el = this.$refs.logContainer;
            if (el && el.scrollTop < 30) this.unseenLogs = 0;
        },
        openFlyout(id) {
            // When switching directly from one flyout to another, suppress the
            // slide transition so panels don't re-animate across the viewport —
            // feels like an in-place content swap. First-open and final-close
            // keep their slide.
            if (this.openFly && this.openFly !== id) {
                const root = document.documentElement;
                root.classList.add('no-fly-transition');
                this.openFly = id;
                this.$nextTick(() => {
                    // Force a reflow so the position change commits without a
                    // transition, then re-enable transitions on the next frame.
                    void root.offsetHeight;
                    requestAnimationFrame(() => {
                        root.classList.remove('no-fly-transition');
                    });
                });
            } else {
                this.openFly = this.openFly === id ? null : id;
            }
        },
        closeFlyouts() {
            this.openFly = null;
        },
        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', this.theme);
            store.set('userEnvTheme', this.theme);
        },
        copyToClipboard(text) {
            const done = () => {
                this.copyFlash = text;
                setTimeout(() => {
                    if (this.copyFlash === text) this.copyFlash = null;
                }, 2500);
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(done).catch(() => {
                    this.showNotification("Clipboard access denied.", true);
                });
            } else {
                // Fallback for older browsers / insecure contexts.
                const ta = document.createElement("textarea");
                ta.value = text;
                ta.style.position = "fixed";
                ta.style.top = "-1000px";
                document.body.appendChild(ta);
                ta.select();
                try {
                    document.execCommand("copy");
                    done();
                } catch (e) {
                    this.showNotification("Copy not supported.", true);
                }
                document.body.removeChild(ta);
            }
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
