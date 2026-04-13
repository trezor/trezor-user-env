import React from 'react';
import { EmulatorCommandsState } from '../types';

interface EmulatorCommandsSectionProps {
  emulatorCommands: EmulatorCommandsState;
  setEmulatorCommands: (commands: EmulatorCommandsState) => void;
  enablePassphrase: boolean;
  setEnablePassphrase: (enable: boolean) => void;
  onWipe: () => void;
  onPressYes: () => void;
  onPressNo: () => void;
  onSetup: (seedName?: string) => void;
  onResetDevice: () => void;
  onResetDeviceShamir: () => void;
  onReadAndConfirmMnemonic: () => void;
  onAllowUnsafe: () => void;
  onReadAndConfirmMnemonicShamir: () => void;
  onSetBackupState: () => void;
  onGetFeatures: () => void;
}

export const EmulatorCommandsSection: React.FC<EmulatorCommandsSectionProps> = ({
  emulatorCommands,
  setEmulatorCommands,
  enablePassphrase,
  setEnablePassphrase,
  onWipe,
  onPressYes,
  onPressNo,
  onSetup,
  onResetDevice,
  onResetDeviceShamir,
  onReadAndConfirmMnemonic,
  onAllowUnsafe,
  onReadAndConfirmMnemonicShamir,
  onSetBackupState,
  onGetFeatures
}) => {
  return (
    <section>
      <h3>Emulator commands</h3>
      <div className="explain-note">
        These commands are auto-confirmed using the emulator's debug link.
      </div>
      <br />
      <div>
        <div className="wipe-yes-no">
          <button onClick={onWipe}>Wipe</button>
          <div>
            <button className="positive" onClick={onPressYes}>
              Press yes
            </button>
            <button className="negative" onClick={onPressNo}>
              Press no
            </button>
          </div>
        </div>
        <input
          id="enablePassphrase"
          type="checkbox"
          checked={enablePassphrase}
          onChange={(e) => setEnablePassphrase(e.target.checked)}
        />
        <label
          className="underlined"
          title="Passphrase protection will be enabled with loading seed."
          htmlFor="enablePassphrase"
        >
          Enable passphrase protection with Load
        </label>
        <br />
        <input
          type="text"
          placeholder="input seed"
          value={emulatorCommands.seed}
          onChange={(e) =>
            setEmulatorCommands({ ...emulatorCommands, seed: e.target.value })
          }
        />
        <button onClick={() => onSetup()}>Load seed</button>
        <br />
        <button onClick={() => onSetup('all')}>Load ALL seed</button>
        <button onClick={() => onSetup('academic')}>Load ACADEMIC seed</button>
      </div>
      <div>
        <button onClick={onResetDevice}>Reset</button>
        <button onClick={onResetDeviceShamir}>Reset with Shamir</button>
      </div>
      <div>
        <button onClick={onReadAndConfirmMnemonic}>
          Read and confirm mnemonic
        </button>
        <br />
        <button onClick={onAllowUnsafe}>Allow unsafe (safety checks)</button>
      </div>
      <div>
        <label htmlFor="shares-input">Shares</label>
        <input
          id="shares-input"
          type="number"
          value={emulatorCommands.shamirShares}
          size={3}
          min={1}
          max={20}
          onChange={(e) =>
            setEmulatorCommands({
              ...emulatorCommands,
              shamirShares: parseInt(e.target.value)
            })
          }
        />
        <label htmlFor="threshold-input">Threshold</label>
        <input
          id="threshold-input"
          type="number"
          value={emulatorCommands.shamirThreshold}
          size={3}
          min={1}
          max={20}
          onChange={(e) =>
            setEmulatorCommands({
              ...emulatorCommands,
              shamirThreshold: parseInt(e.target.value)
            })
          }
        />
        <button onClick={onReadAndConfirmMnemonicShamir}>
          Read and confirm mnemonic Shamir
        </button>
      </div>
      <div>
        <button onClick={onSetBackupState}>Set backup state</button>
      </div>
      <div>
        <button onClick={onGetFeatures}>Get features</button>
      </div>
    </section>
  );
};
