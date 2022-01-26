/* eslint-disable func-names */
/* eslint-disable @typescript-eslint/camelcase */
/* eslint-disable no-underscore-dangle */
const websocketUrl = 'ws://localhost:9001/';
const backgroundCheckPeriod = 500;
const templateJSON = '{"type": "specify"}';

let ws;
let id = 0;

function output(text, color = 'black') {
    const log = document.getElementById('log');
    const escapedText = text
        .replace(/&/, '&amp;')
        .replace(/</, '&lt;')
        .replace(/>/, '&gt;')
        .replace(/"/, '&quot;'); // "
    log.innerHTML = `<span style="color: ${color};">${currentTime()} - ${escapedText}</span><br>${log.innerHTML}`;
}

const currentTime = () => {
    const now = new Date();
    const hours = ('0' + now.getHours()).slice(-2)
    const minutes = ('0' + now.getMinutes()).slice(-2)
    const seconds = ('0' + now.getSeconds()).slice(-2)
    return `${hours}:${minutes}:${seconds}`;
}

const createOption = (select, value) => {
    const option = document.createElement('option');
    option.text = value;
    option.value = value;
    select.add(option);
};

const clearOptions = (select) => {
    while (select.options.length) {
        select.remove(0);
    }
};

const populateEmulatorSelect = (firmwares) => {
    const t1Select = document.getElementById('t1-select');
    const t2Select = document.getElementById('t2-select');
    clearOptions(t1Select);
    clearOptions(t2Select);
    firmwares['T1'].forEach(version => createOption(t1Select, version));
    firmwares['TT'].forEach(version => createOption(t2Select, version));
};


const handleMessage = (event) => {
    if (!event.data || typeof event.data !== 'string') {
        output(`Response received without proper data: ${event.data}`, 'red');
        return;
    }

    const dataObject = JSON.parse(event.data);

    // When the check is happening on the background (not forced by user),
    //   do not print anything to the Log (but perform the UI update)
    if ('background_check' in dataObject && dataObject.background_check) {
        reflectBackgroundSituationInGUI(dataObject);
        return;
    }

    // Choosing the right color for the output - normal, success and error scenarios
    let color = 'black';
    if ('success' in dataObject) {
        if (dataObject.success) {
            color = 'green';
        } else {
            color = 'red';
            alert('Some error happened, please look into Log below.');
        }
    }

    output(`Response received: ${event.data}`, color);

    if (dataObject.type === 'client') {
        populateEmulatorSelect(dataObject.firmwares);
    }
};

function init() {
    // Connect to Web Socket
    ws = new WebSocket(websocketUrl);
    // Set event handlers.
    ws.onopen = function () {
        document.getElementById('ws-status').style.display = 'none';
        output('Websocket opened');
    };
    ws.onmessage = handleMessage;
    ws.onclose = function () {
        document.getElementById('ws-status').style.display = 'block';
        output('Websocket closed');
    };
    ws.onerror = function (e) {
        output('onerror - please look into the console');
        console.log(e);
    };
}

function _send(json) {
    const requestToSend = JSON.stringify(
        Object.assign(json, {
            id,
        }),
    );
    ws.send(requestToSend);
    id++;
    output(`Request sent: ${requestToSend}`, 'blue');
}

function _sendOnBackground(json) {
    ws.send(JSON.stringify(json));
}

function onSubmit() {
    const input = document.getElementById('raw-input');

    // Defending against invalid JSON
    try {
        JSON.parse(input.value);
    } catch (err) {
        alert('Invalid JSON provided!');
        return;
    }

    output(`Sent manually: ${input.value}`, 'magenta');
    _send(JSON.parse(input.value));
    input.focus();
}

function onCloseClick() {
    ws.close();
}

function emulatorStart(select) {
    const version = document.getElementById(select).value;
    const wipe = document.getElementById("wipeDevice").checked;
    const output_to_logfile = document.getElementById("emulatorUseLogfile").checked;
    const save_screenshots = document.getElementById("emulatorSaveScreenshots").checked;
    _send({
        type: 'emulator-start',
        version,
        wipe,
        output_to_logfile,
        save_screenshots,
    });
}

function emulatorStartFromUrl() {
    let url = document.getElementById("emu-url").value;
    if (!url) {
        alert("URL is empty!");
        return
    }

    // Taking the last character - "1" or "2" from the model
    const model = document.getElementById("emu-url-model-select").value.substr(-1);
    const urlFormat = document.getElementById("emu-url-format-select").value;
    const wipe = document.getElementById("wipeDevice").checked;
    const output_to_logfile = document.getElementById("emulatorUseLogfile").checked;

    const gitlabJobPrefix = "https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs"
    const T1PathSuffix = "artifacts/raw/legacy/firmware/trezor.elf"
    const T2PathSuffix = "artifacts/raw/core/build/unix/trezor-emu-core"

    // URL might need some processing in case it is not complete
    // (Yes, handling URLs as strings is not very good, but should be alright in this easy case)
    if (urlFormat === "Gitlab job link") {
        // Getting rid of possible slash at the end
        if (url.substr(-1) === "/") {
            url = url.slice(0, -1);
        }

        if (model === "1") {
            url = `${url}/${T1PathSuffix}`
        } else {
            url = `${url}/${T2PathSuffix}`
        }
    } else if (urlFormat === "Gitlab job ID") {
        if (model === "1") {
            url = `${gitlabJobPrefix}/${url}/${T1PathSuffix}`
        } else {
            url = `${gitlabJobPrefix}/${url}/${T2PathSuffix}`
        }
    }

    _send({
        type: 'emulator-start-from-url',
        url,
        model,
        wipe,
        output_to_logfile,
    });
}

function emulatorWipe() {
    _send({
        type: 'emulator-wipe',
    });
}

function emulatorResetDevice() {
    _send({
        type: 'emulator-reset-device',
    });
}

function emulatorSetup() {
    const input = document.getElementById('seed-input');
    _send({
        type: 'emulator-setup',
        mnemonic: input.value || 'all all all all all all all all all all all all',
        pin: '',
        passphrase_protection: false,
        label: 'Hello!',
    });
}

function emulatorPressYes() {
    _send({
        type: 'emulator-press-yes',
    });
}

function emulatorPressNo() {
    _send({
        type: 'emulator-press-no',
    });
}

function emulatorAllowUnsafe() {
    _send({
        type: 'emulator-allow-unsafe-paths',
    });
}

function emulatorStop() {
    _send({
        type: 'emulator-stop',
    });
}

function emulatorGetScreenshot() {
    _send({
        type: 'emulator-get-screenshot',
    });
}

function bridgeStart(version) {
    const output_to_logfile = document.getElementById("bridgeUseLogfile").checked;
    _send({
        type: 'bridge-start',
        version,
        output_to_logfile,
    });
}

function bridgeStop() {
    _send({
        type: 'bridge-stop',
    });
}

function exit() {
    _send({
        type: 'exit',
    });
}

function ping() {
    _send({
        type: 'ping',
    });
}

function readAndConfirmMnemonic() {
    _send({
        type: 'emulator-read-and-confirm-mnemonic',
    });
}

function readAndConfirmMnemonicShamir() {
    const shares = parseInt(document.getElementById("shares-input").value);
    const threshold = parseInt(document.getElementById("threshold-input").value);
    _send({
        type: 'emulator-read-and-confirm-shamir-mnemonic',
        shares,
        threshold,
    });
}

function reflectBackgroundSituationInGUI(dataObject) {
    if ('bridge_status' in dataObject) {
        reflectBridgeSituation(dataObject.bridge_status);
    }
    if ('emulator_status' in dataObject) {
        reflectEmulatorSituation(dataObject.emulator_status);
    }
}

function reflectBridgeSituation(status) {
    if (status.is_running) {
        // Can happen that bridge is already running on the background, but
        //   was not spawned by the GUI (causing confusion)
        if (!status.version) {
            alert('It seems you already have an instance of bridge running - please kill it.');
        }
        writeBridgeStatus(`Running - ${status.version}`, 'green');
    } else {
        writeBridgeStatus('Stopped', 'red');
    }
}

function reflectEmulatorSituation(status) {
    if (status.is_running) {
        writeEmulatorStatus(`Running - ${status.version}`, 'green');
    } else {
        writeEmulatorStatus('Stopped', 'red');
    }
}

function getBackgroundStatus() {
    _sendOnBackground({
        type: 'background-check',
    });
}

function writeBridgeStatus(status, color = 'black') {
    document.getElementById('bridge-status').innerHTML = status;
    document.getElementById('bridge-status-line').style["color"] = color;
}

function writeEmulatorStatus(status, color = 'black') {
    document.getElementById('emu-status').innerHTML = status;
    document.getElementById('emu-status-line').style["color"] = color;
}

function watchBackgroundStatus() {
    setInterval(getBackgroundStatus, backgroundCheckPeriod);
}

window.onload = function () {
    init();
    watchBackgroundStatus();
    document.getElementById('raw-input').value = templateJSON;

    const t1orT2Select = document.getElementById('emu-url-model-select');
    createOption(t1orT2Select, "T2")
    createOption(t1orT2Select, "T1")

    const urlFormatSelect = document.getElementById('emu-url-format-select');
    createOption(urlFormatSelect, "Gitlab job link")
    createOption(urlFormatSelect, "Gitlab job ID")
    createOption(urlFormatSelect, "Custom link")
};
