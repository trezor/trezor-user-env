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

const sortVersion = arr => {
    return arr
        .map(a => a.replace(/\d+/g, n => +n + 100000))
        .sort()
        .map(a => a.replace(/\d+/g, n => +n - 100000))
        .reverse();
};

const createOption = (select, value) => {
    const option = document.createElement("option");
    option.text = value;
    option.value = value;
    select.appendChild(option);
}

const populateEmulatorSelect = (data) => {
    const t1Select = document.getElementById('t1-select');
    const t2Select = document.getElementById('t2-select');
    const t1Options = sortVersion([
        '1.6.2',
        '1.6.3',
        '1.7.0',
        '1.7.1',
        '1.7.2',
        '1.7.3',
        '1.8.0',
        '1.8.1',
        '1.8.2',
        '1.8.3',
        '1.9.0',
        '1.9.1',
        '1.9.2',
        '1.9.3',
        '1-master',
    ]).forEach(version => createOption(t1Select, version));

    const t2Options = sortVersion([
        '2.0.8',
        '2.0.9',
        '2.0.10',
        '2.1.0',
        '2.1.1',
        '2.1.2',
        '2.1.3',
        '2.1.4',
        '2.1.5',
        '2.1.6',
        '2.1.7',
        '2.1.8',
        '2.2.0',
        '2.3.0',
        '2.3.1',
        '2.3.2',
        '2.3.3',
        '2-master',
    ]).forEach(version => createOption(t2Select, version));
}


const handleMessage = event => {
    output(`onmessage: ${event.data}`);
    if (!event.data || typeof event.data !== 'string') return;

    const data = JSON.parse(event.data);

    if (data.type === 'client') {
        populateEmulatorSelect(data.emulators);
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
    const input = document.getElementById('input');
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
    _send({
        type: 'emulator-setup',
        mnemonic: 'all all all all all all all all all all all all',
        pin: '',
        passphrase_protection: false,
        label: 'Hello!',
    });
}

function emulatorDecision() {
    _send({
        type: 'emulator-decision',
    });
}

function emulatorStop() {
    _send({
        type: 'emulator-stop',
    });
}

function bridgeStart() {
    _send({
        type: 'bridge-start',
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
