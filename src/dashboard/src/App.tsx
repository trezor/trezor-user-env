import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { Notification } from './components/Notification';
import { BridgeSection } from './components/BridgeSection';
import { TropicSection } from './components/TropicSection';
import { EmulatorSection } from './components/EmulatorSection';
import { EmulatorCommandsSection } from './components/EmulatorCommandsSection';
import { RegtestSection } from './components/RegtestSection';
import { ServerSection } from './components/ServerSection';
import { EventLogSection } from './components/EventLogSection';
import {
  BridgeState,
  TropicState,
  EmulatorsState,
  EmulatorUrlState,
  EmulatorBranchState,
  EmulatorCommandsState,
  RegtestState,
  ServerState,
  NotificationState,
  BackgroundCheckData,
  ClientResponseData,
  ServerResponse
} from './types';
import '../css/index.css';

function App(): React.ReactElement {
  const {
    ws,
    isWaitingForResponse,
    setIsWaitingForResponse,
    logs,
    logEvent,
    setupWebSocket,
    sendMessage,
    sendMessageOnBackground,
    closeWebsocket,
    BACKGROUND_CHECK_PERIOD_MS
  } = useWebSocket();

  const [bridges, setBridges] = useState<BridgeState>({
    versions: [],
    selected: '',
    outputToLogfile: false,
    status: 'unknown',
    statusColor: 'black',
    hasSuiteLocal: false
  });

  const [tropic, setTropic] = useState<TropicState>({
    outputToLogfile: true,
    status: 'unknown',
    statusColor: 'black'
  });

  const [emulators, setEmulators] = useState<EmulatorsState>({
    versions: {
      T1B1: {
        header: 'Trezor One',
        versions: [],
        selected: ''
      },
      T2T1: {
        header: 'Trezor T',
        versions: [],
        selected: ''
      },
      T3B1: {
        header: 'Trezor Safe 3',
        versions: [],
        selected: ''
      },
      T3T1: {
        header: 'Trezor Safe 5',
        versions: [],
        selected: ''
      },
      T3W1: {
        header: 'Trezor Safe 7',
        versions: [],
        selected: ''
      }
    },
    wipeDevice: false,
    screenshotMode: false,
    animations: false,
    outputToLogfile: false,
    status: 'unknown',
    statusColor: 'black'
  });

  const [emulatorUrl, setEmulatorUrl] = useState<EmulatorUrlState>({
    url: '',
    model: ''
  });

  const [emulatorBranch, setEmulatorBranch] = useState<EmulatorBranchState>({
    branch: '',
    model: '',
    btcOnly: false
  });

  const [emulatorDownloadMessage, setEmulatorDownloadMessage] = useState('');

  const [emulatorCommands, setEmulatorCommands] = useState<EmulatorCommandsState>({
    seed: '',
    shamirShares: 3,
    shamirThreshold: 2
  });

  const [enablePassphrase, setEnablePassphrase] = useState(true);

  const [regtest, setRegtest] = useState<RegtestState>({
    status: 'unknown',
    statusColor: 'black',
    mineBlocks: 1,
    mineAddress: '',
    sendAmount: 10,
    sendAddress: ''
  });

  const [server, setServer] = useState<ServerState>({
    command: '{"type": "specify"}'
  });

  const [notifications, setNotifications] = useState<NotificationState>({
    showPopup: false,
    text: '',
    header: 'Notification',
    isError: false
  });

  const wsRef = useRef<WebSocket | null>(null);

  const showNotification = useCallback((text: string, isError = false) => {
    setNotifications({
      text,
      showPopup: true,
      isError,
      header: isError ? 'Error' : 'Notification'
    });
  }, []);

  const reflectBackgroundSituationInGUI = useCallback((dataObject: BackgroundCheckData) => {
    if ('bridge_status' in dataObject && dataObject.bridge_status) {
      const status = dataObject.bridge_status;
      if (status.is_running) {
        if (!status.version) {
          showNotification(
            'It seems you already have an instance of bridge running - please kill it. `ps -ef | grep trezor` ... `kill <pid>`',
            true
          );
        }
        setBridges(prev => ({
          ...prev,
          status: `Running - ${status.version}`,
          statusColor: 'green'
        }));
      } else {
        setBridges(prev => ({
          ...prev,
          status: 'Stopped',
          statusColor: 'red'
        }));
      }
    }

    if ('emulator_status' in dataObject && dataObject.emulator_status) {
      const status = dataObject.emulator_status;
      if (status.is_running) {
        setEmulators(prev => ({
          ...prev,
          status: `Running - ${status.version}`,
          statusColor: 'green'
        }));
      } else {
        setEmulators(prev => ({
          ...prev,
          status: 'Stopped',
          statusColor: 'red'
        }));
      }
    }

    if ('tropic_status' in dataObject && dataObject.tropic_status) {
      const status = dataObject.tropic_status;
      if (status.is_running) {
        setTropic(prev => ({
          ...prev,
          status: `Running - ${status.version}`,
          statusColor: 'green'
        }));
      } else {
        setTropic(prev => ({
          ...prev,
          status: 'Stopped',
          statusColor: 'red'
        }));
      }
    }

    if ('regtest_status' in dataObject) {
      const isRunning = dataObject.regtest_status;
      if (isRunning) {
        setRegtest(prev => ({
          ...prev,
          status: 'Running',
          statusColor: 'green'
        }));
      } else {
        setRegtest(prev => ({
          ...prev,
          status: 'Stopped',
          statusColor: 'red'
        }));
      }
    }
  }, [showNotification]);

  // Update emulator model from URL
  useEffect(() => {
    if (emulatorUrl.url) {
      Object.keys(emulators.versions).forEach((model) => {
        if (emulatorUrl.url.toLowerCase().includes(model.toLowerCase())) {
          setEmulatorUrl(prev => ({ ...prev, model }));
        }
      });
    }
  }, [emulatorUrl.url, emulators.versions]);

  // Setup WebSocket message handler
  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const dataObject: ServerResponse = JSON.parse(event.data);

        if ('background_check' in dataObject) {
          reflectBackgroundSituationInGUI(dataObject as BackgroundCheckData);
          return;
        }

        setIsWaitingForResponse(false);

        let color = 'black';
        if ('success' in dataObject) {
          if (dataObject.success) {
            color = 'green';
          } else {
            color = 'red';
            showNotification(
              'Some error happened, please look into Log below.',
              true
            );
            setEmulatorDownloadMessage('');
          }
        }

        if (
          'response' in dataObject &&
          typeof dataObject.response === 'string' &&
          dataObject.response.includes('Emulator downloaded')
        ) {
          setEmulatorDownloadMessage('');
        }

        logEvent(`Response received: ${event.data}`, color);

        // Filling the possible options for the emulators/bridges
        if (dataObject.type === 'client' && 'firmwares' in dataObject && 'bridges' in dataObject) {
          const clientData = dataObject as unknown as ClientResponseData;
          setEmulators(prevEmulators => {
            const newEmulators = { ...prevEmulators };
            for (const model in clientData.firmwares) {
              const options = clientData.firmwares[model];
              newEmulators.versions[model].versions = options;
              newEmulators.versions[model].selected = options[0];
            }
            return newEmulators;
          });

          const nodebridge: string[] = [];
          const legacy: string[] = [];
          clientData.bridges.forEach((b) =>
            b.startsWith('2.') ? legacy.push(b) : nodebridge.push(b)
          );
          const allBridges = nodebridge.concat(legacy);
          
          setBridges(prev => ({
            ...prev,
            versions: allBridges,
            selected: allBridges[0],
            hasSuiteLocal: clientData.bridges.includes('local-suite-node-bridge')
          }));
        }
      } catch (err) {
        logEvent(`Response received is not a valid JSON: ${event.data}`, 'red');
      }
    };

    ws.onmessage = handleMessage;
    wsRef.current = ws;
  }, [ws, logEvent, setIsWaitingForResponse, showNotification, reflectBackgroundSituationInGUI, setEmulators, setBridges, setEmulatorDownloadMessage]);

  // Setup background status check
  useEffect(() => {
    const interval = setInterval(() => {
      sendMessageOnBackground({
        type: 'background-check'
      });
    }, BACKGROUND_CHECK_PERIOD_MS);

    return () => clearInterval(interval);
  }, [sendMessageOnBackground, BACKGROUND_CHECK_PERIOD_MS]);

  // Setup WebSocket on mount
  useEffect(() => {
    setupWebSocket();
    
    // Make app visible
    const appElement = document.getElementById('app');
    if (appElement) {
      appElement.style.display = 'block';
    }

    // Listen for Esc key to close notification
    const handleKeyDown = (event: KeyboardEvent) => {
      if (notifications.showPopup && event.key === 'Escape') {
        setNotifications(prev => ({ ...prev, showPopup: false }));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setupWebSocket, notifications.showPopup]);

  // Bridge actions
  const bridgeStart = () => {
    sendMessage({
      type: 'bridge-start',
      version: bridges.selected,
      output_to_logfile: bridges.outputToLogfile
    });
  };

  const bridgeStop = () => {
    sendMessage({
      type: 'bridge-stop'
    });
  };

  // Tropic actions
  const tropicStart = () => {
    sendMessage({
      type: 'tropic-start',
      output_to_logfile: tropic.outputToLogfile
    });
  };

  const tropicStop = () => {
    sendMessage({
      type: 'tropic-stop'
    });
  };

  // Emulator actions
  const emulatorStart = (model: string) => {
    const emulator = emulators.versions[model];
    if (!emulator) {
      showNotification('No emulator selected', true);
      return;
    }
    if (!emulator.selected) {
      showNotification('Please select a version first', true);
      return;
    }

    sendMessage({
      type: 'emulator-start',
      version: emulator.selected,
      model,
      wipe: emulators.wipeDevice,
      output_to_logfile: emulators.outputToLogfile,
      save_screenshots: emulators.screenshotMode,
      show_animations: emulators.animations
    });
  };

  const emulatorStartFromUrl = () => {
    const url = emulatorUrl.url;
    if (!url) {
      showNotification('URL is empty!', true);
      return;
    }

    const model = emulatorUrl.model;
    if (!model) {
      showNotification('Model is empty!', true);
      return;
    }

    sendMessage({
      type: 'emulator-start-from-url',
      url,
      model,
      wipe: emulators.wipeDevice,
      output_to_logfile: emulators.outputToLogfile,
      save_screenshots: emulators.screenshotMode,
      show_animations: emulators.animations
    });

    setEmulatorDownloadMessage(
      'Emulator started downloading, it may take a while...'
    );
  };

  const emulatorStartFromBranch = () => {
    const branch = emulatorBranch.branch;
    if (!branch) {
      showNotification('Branch is empty!', true);
      return;
    }

    const model = emulatorBranch.model;
    if (!model) {
      showNotification('Model is empty!', true);
      return;
    }

    sendMessage({
      type: 'emulator-start-from-branch',
      branch,
      model,
      btc_only: emulatorBranch.btcOnly,
      wipe: emulators.wipeDevice,
      output_to_logfile: emulators.outputToLogfile,
      save_screenshots: emulators.screenshotMode,
      show_animations: emulators.animations
    });

    setEmulatorDownloadMessage(
      'Emulator started downloading, it may take a while...'
    );
  };

  const emulatorStop = () => {
    sendMessage({
      type: 'emulator-stop'
    });
  };

  // Emulator commands
  const emulatorWipe = () => {
    sendMessage({
      type: 'emulator-wipe'
    });
  };

  const emulatorPressYes = () => {
    sendMessage({
      type: 'emulator-press-yes'
    });
  };

  const emulatorPressNo = () => {
    sendMessage({
      type: 'emulator-press-no'
    });
  };

  const emulatorSetup = (seedName = '') => {
    const mapping: { [key: string]: string } = {
      all: 'all all all all all all all all all all all all',
      academic:
        'academic again academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic pecan provide remember'
    };

    const seed = mapping[seedName] || emulatorCommands.seed;
    if (!seed) {
      showNotification('Please enter a seed', true);
      return;
    }
    sendMessage({
      type: 'emulator-setup',
      mnemonic: seed,
      pin: '',
      passphrase_protection: enablePassphrase,
      label: 'Hello!'
    });
  };

  const emulatorResetDevice = () => {
    sendMessage({
      type: 'emulator-reset-device'
    });
  };

  const emulatorResetDeviceShamir = () => {
    sendMessage({
      type: 'emulator-reset-device',
      use_shamir: true
    });
  };

  const readAndConfirmMnemonic = () => {
    sendMessage({
      type: 'emulator-read-and-confirm-mnemonic'
    });
  };

  const emulatorAllowUnsafe = () => {
    sendMessage({
      type: 'emulator-allow-unsafe-paths'
    });
  };

  const readAndConfirmMnemonicShamir = () => {
    sendMessage({
      type: 'emulator-read-and-confirm-shamir-mnemonic',
      shares: emulatorCommands.shamirShares,
      threshold: emulatorCommands.shamirThreshold
    });
  };

  const emulatorSetBackupState = () => {
    sendMessage({
      type: 'emulator-set-for-backup'
    });
  };

  const emulatorGetFeatures = () => {
    sendMessage({
      type: 'emulator-get-features'
    });
  };

  // Regtest actions
  const regtestMine = () => {
    sendMessage({
      type: 'regtest-mine-blocks',
      block_amount: regtest.mineBlocks,
      address: regtest.mineAddress
    });
  };

  const regtestSend = () => {
    sendMessage({
      type: 'regtest-send-to-address',
      btc_amount: regtest.sendAmount,
      address: regtest.sendAddress
    });
  };

  // Server actions
  const sendServerCommand = () => {
    const command = server.command;
    try {
      JSON.parse(command);
    } catch (err) {
      showNotification('Invalid JSON provided!', true);
      return;
    }

    logEvent(`Sent manually: ${command}`, 'magenta');
    sendMessage(JSON.parse(command));
  };

  const ping = () => {
    sendMessage({
      type: 'ping'
    });
  };

  const exit = () => {
    sendMessage({
      type: 'exit'
    });
  };

  return (
    <div id="app">
      <Notification
        notification={notifications}
        onClose={() => setNotifications({ ...notifications, showPopup: false })}
      />

      {isWaitingForResponse && (
        <div className="waiting-for-response">
          WAITING FOR RESPONSE (ignoring all inputs)
        </div>
      )}

      {!ws && (
        <div id="ws-status">
          <div>
            Websocket server not connected.
            <button onClick={setupWebSocket}>Connect</button>
          </div>
        </div>
      )}

      <div className="sections-container">
        <BridgeSection
          bridges={bridges}
          setBridges={setBridges}
          onStart={bridgeStart}
          onStop={bridgeStop}
        />

        <TropicSection
          tropic={tropic}
          setTropic={setTropic}
          onStart={tropicStart}
          onStop={tropicStop}
        />

        <EmulatorSection
          emulators={emulators}
          setEmulators={setEmulators}
          emulatorUrl={emulatorUrl}
          setEmulatorUrl={setEmulatorUrl}
          emulatorBranch={emulatorBranch}
          setEmulatorBranch={setEmulatorBranch}
          emulatorDownloadMessage={emulatorDownloadMessage}
          onStart={emulatorStart}
          onStartFromUrl={emulatorStartFromUrl}
          onStartFromBranch={emulatorStartFromBranch}
          onStop={emulatorStop}
        />

        <EmulatorCommandsSection
          emulatorCommands={emulatorCommands}
          setEmulatorCommands={setEmulatorCommands}
          enablePassphrase={enablePassphrase}
          setEnablePassphrase={setEnablePassphrase}
          onWipe={emulatorWipe}
          onPressYes={emulatorPressYes}
          onPressNo={emulatorPressNo}
          onSetup={emulatorSetup}
          onResetDevice={emulatorResetDevice}
          onResetDeviceShamir={emulatorResetDeviceShamir}
          onReadAndConfirmMnemonic={readAndConfirmMnemonic}
          onAllowUnsafe={emulatorAllowUnsafe}
          onReadAndConfirmMnemonicShamir={readAndConfirmMnemonicShamir}
          onSetBackupState={emulatorSetBackupState}
          onGetFeatures={emulatorGetFeatures}
        />

        <RegtestSection
          regtest={regtest}
          setRegtest={setRegtest}
          onMine={regtestMine}
          onSend={regtestSend}
        />

        <ServerSection
          server={server}
          setServer={setServer}
          onSendCommand={sendServerCommand}
          onPing={ping}
          onExit={exit}
          onCloseWebsocket={closeWebsocket}
        />

        <EventLogSection logs={logs} />
      </div>
    </div>
  );
}

export default App;
