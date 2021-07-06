/* eslint-disable func-names */
/* eslint-disable @typescript-eslint/camelcase */
/* eslint-disable no-underscore-dangle */
const websocketUrl = 'ws://localhost:9001/';
const backgroundCheckPeriod = 3000;
const templateJSON = '{"type": "specify"}'

let ws;
let id = 0;

function output(str, color = 'black') {
    const log = document.getElementById('log');
    const escaped = str
        .replace(/&/, '&amp;')
        .replace(/</, '&lt;')
        .replace(/>/, '&gt;')
        .replace(/"/, '&quot;'); // "
    log.innerHTML = `<span style="color: ${color};">${escaped}</span><br>${log.innerHTML}`;
}

const createOption = (select, value) => {
    const option = document.createElement("option");
    option.text = value;
    option.value = value;
    select.add(option);
}

const clearOptions = select => {
    while(select.options.length) select.remove(0);
}

const populateEmulatorSelect = firmwares => {
    const t1Select = document.getElementById('t1-select');
    const t2Select = document.getElementById('t2-select');
    clearOptions(t1Select);
    clearOptions(t2Select);
    firmwares["T1"].forEach(version => createOption(t1Select, version));
    firmwares["TT"].forEach(version => createOption(t2Select, version));
}


const handleMessage = event => {
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
            alert("Some error happened, please look into Log below.")
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
        output('onerror');
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
    } catch(err) {
        alert('Impossible to parse input into JSON! Please correct the input string');
        return;
    }

    output(`Sent manually: ${input.value}`, 'magenta');
    _send(JSON.parse(input.value));
    // TODO: do we even want to revert to default one, would not
    //   it be better to just leave it, so user can modify it?
    input.value = templateJSON;
    input.focus();
}

function onCloseClick() {
    ws.close();
}

function emulatorStart(select) {
    const version = document.getElementById(select).value;
    _send({
        type: 'emulator-start',
        version,
    });
    setTimeout(getBackgroundStatus, 200);
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

function emulatorStop() {
    _send({
        type: 'emulator-stop',
    });
    setTimeout(getBackgroundStatus, 200);
}

function bridgeStart(version) {
    _send({
        type: 'bridge-start',
        version,
    });
    setTimeout(getBackgroundStatus, 200);
}

function bridgeStop() {
    _send({
        type: 'bridge-stop',
    });
    setTimeout(getBackgroundStatus, 200);
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
        reflectBridgeStartedInGUI(status.version);
        writeBridgeStatus(`Running - ${status.version}`);
    } else {
        reflectBridgeStoppedInGUI();
        writeBridgeStatus("Stopped");
    }
}

function reflectBridgeStartedInGUI(version) {
    // Can happen that bridge is already running on the background, but
    //   was not spawned by the GUI (causing confusion)
    if (!version) {
        alert("Please check if there is no instance of bridge running already - please kill them.");
        return;
    }

    const btnIdToHighlight = `bridge-${version}`
    document.querySelectorAll('.bridge-button').forEach(function (btn) {
        btn.style.backgroundColor = "grey";
    });
    document.getElementById(btnIdToHighlight).style.backgroundColor = "green";
    document.getElementById(`bridge-stop`).style.backgroundColor = "grey";
}

function reflectBridgeStoppedInGUI() {
    document.querySelectorAll('.bridge-button').forEach(function (btn) {
        btn.style.backgroundColor = "grey";
    });
    document.getElementById(`bridge-stop`).style.backgroundColor = "red";
}

function reflectEmulatorSituation(status) {
    if (status.is_running) {
        reflectEmulatorStartedInGUI(status.version);
        writeEmulatorStatus(`Running - ${status.version}`);
    } else {
        reflectEmulatorStoppedInGUI();
        writeEmulatorStatus("Stopped");
    }
}

function reflectEmulatorStartedInGUI(version) {
    const versionNumber = version.charAt(0);
    const btnIdToHighlight = `emu-${versionNumber}-start`;
    document.querySelectorAll('.emu-buttons').forEach(function (btn) {
        btn.style.backgroundColor = "grey";
    });
    document.getElementById(btnIdToHighlight).style.backgroundColor = "green";
    document.getElementById("emu-stop").style.backgroundColor = "grey";
}

function reflectEmulatorStoppedInGUI() {
    document.querySelectorAll('.emu-buttons').forEach(function (btn) {
        btn.style.backgroundColor = "grey";
    });
    document.getElementById("emu-stop").style.backgroundColor = "red";
}

function getBackgroundStatus() {
    _sendOnBackground({type: 'background-check'})
}

function writeBridgeStatus(status) {
    const el = document.getElementById('bridge-status');
    el.innerHTML = status;
}

function writeEmulatorStatus(status) {
    const el = document.getElementById('emulator-status');
    el.innerHTML = status;
}

// maybe not the best idea to bombard bridge with status requests. time will show.
function watchBackgroundStatus() {
    setTimeout(getBackgroundStatus, 200)
    setInterval(getBackgroundStatus, backgroundCheckPeriod);
}

window.onload = function () {
    init();
    watchBackgroundStatus();
    document.getElementById('raw-input').value = templateJSON;
}
