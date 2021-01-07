/* eslint-disable func-names */
/* eslint-disable @typescript-eslint/camelcase */
/* eslint-disable no-underscore-dangle */
let ws;
let id = 0;
let bridge = false;

function output(str) {
    const log = document.getElementById('log');
    const escaped = str
        .replace(/&/, '&amp;')
        .replace(/</, '&lt;')
        .replace(/>/, '&gt;')
        .replace(/"/, '&quot;'); // "
    log.innerHTML = `${escaped}<br>${log.innerHTML}`;
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
    output(`onmessage: ${event.data}`);
    if (!event.data || typeof event.data !== 'string') return;

    const data = JSON.parse(event.data);

    if (data.type === 'client') {
        populateEmulatorSelect(data.firmwares);
    }
};

function init() {
    // Connect to Web Socket
    ws = new WebSocket('ws://localhost:9001/');
    // Set event handlers.
    ws.onopen = function () {
        document.getElementById('ws-status').style.display = 'none';
        output('onopen');
    };
    ws.onmessage = handleMessage;
    ws.onclose = function () {
        document.getElementById('ws-status').style.display = 'block';
        output('onclose');
    };
    ws.onerror = function (e) {
        output('onerror');
        console.log(e);
    };
}

function _send(json) {
    ws.send(
        JSON.stringify(
            Object.assign(json, {
                id,
            }),
        ),
    );
    id++;
}

function onSubmit() {
    const input = document.getElementById('raw-input');
    _send(JSON.parse(input.value));
    output(`send: ${input.value}`);
    input.value = '';
    input.focus();
}

function onCloseClick() {
    ws.close();
}

function suiteStart(version) {
    _send({
        type: 'suite-start',
        version,
    });
}

function emulatorStart(select) {
    const version = document.getElementById(select).value;
    _send({
        type: 'emulator-start',
        version,
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

function emulatorStop() {
    _send({
        type: 'emulator-stop',
    });
}

function bridgeStart(version) {
    _send({
        type: 'bridge-start',
        version,
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

function getBridgeStatus() {
    return new Promise((resolve, reject) => {
        fetch('http://0.0.0.0:21325/status/', { mode: 'no-cors' }).then(
            response => {
                bridge = true;
                resolve();
            },
            error => {
                bridge = false;
                reject();
            },
        );
    });
}

function writeBridgeStatus(str) {
    const el = document.getElementById('bridge-status');
    if (bridge) {
        el.innerHTML = 'running';
    } else {
        el.innerHTML = 'stopped';
    }
}

// maybe not the best idea to bombard bridge with status requests. time will show.
function watchBridge() {
    setInterval(() => {
        getBridgeStatus().then(
            () => {
                writeBridgeStatus();
            },
            () => {
                writeBridgeStatus();
            },
        );
    }, 3000);
}

window.onload = function () {
    init();
}
