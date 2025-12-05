import React from 'react';
import { EmulatorsState, EmulatorUrlState, EmulatorBranchState } from '../types';

interface EmulatorSectionProps {
  emulators: EmulatorsState;
  setEmulators: (emulators: EmulatorsState) => void;
  emulatorUrl: EmulatorUrlState;
  setEmulatorUrl: (url: EmulatorUrlState) => void;
  emulatorBranch: EmulatorBranchState;
  setEmulatorBranch: (branch: EmulatorBranchState) => void;
  emulatorDownloadMessage: string;
  onStart: (model: string) => void;
  onStartFromUrl: () => void;
  onStartFromBranch: () => void;
  onStop: () => void;
}

export const EmulatorSection: React.FC<EmulatorSectionProps> = ({
  emulators,
  setEmulators,
  emulatorUrl,
  setEmulatorUrl,
  emulatorBranch,
  setEmulatorBranch,
  emulatorDownloadMessage,
  onStart,
  onStartFromUrl,
  onStartFromBranch,
  onStop
}) => {
  const updateVersion = (model: string, version: string) => {
    setEmulators({
      ...emulators,
      versions: {
        ...emulators.versions,
        [model]: {
          ...emulators.versions[model],
          selected: version
        }
      }
    });
  };

  return (
    <section>
      <h3>Emulator</h3>
      <div className="explain-note">
        Use left and right arrow keys to emulate the Trezor One/Safe3 buttons.
        Mouse clicks for other models.
      </div>

      <br />

      <div style={{ color: emulators.statusColor }}>
        <b>
          Status: <span>{emulators.status}</span>
        </b>
      </div>

      {Object.entries(emulators.versions).map(([model, details]) => (
        <div key={model}>
          <h4>
            {details.header} ({model})
          </h4>
          <select
            value={details.selected}
            onChange={(e) => updateVersion(model, e.target.value)}
          >
            {details.versions.map((version) => (
              <option key={version} value={version}>
                {version}
              </option>
            ))}
          </select>
          <button className="positive" onClick={() => onStart(model)}>
            Start
          </button>
        </div>
      ))}

      <div>
        <input
          id="animations"
          type="checkbox"
          checked={emulators.animations}
          onChange={(e) =>
            setEmulators({ ...emulators, animations: e.target.checked })
          }
        />
        <label className="underlined" title="Animations will be turned on." htmlFor="animations">
          Show animations
        </label>
        <br />
        <input
          id="wipeDevice"
          type="checkbox"
          checked={emulators.wipeDevice}
          onChange={(e) =>
            setEmulators({ ...emulators, wipeDevice: e.target.checked })
          }
        />
        <label
          className="underlined"
          title="Device will be started without seed or any other settings."
          htmlFor="wipeDevice"
        >
          Start with wiped/empty device
        </label>
        <br />
        <input
          id="emulatorUseLogfile"
          type="checkbox"
          checked={emulators.outputToLogfile}
          onChange={(e) =>
            setEmulators({ ...emulators, outputToLogfile: e.target.checked })
          }
        />
        <label
          className="underlined"
          title="Save emulator logs into logfile. Otherwise, logs are shown in console."
          htmlFor="emulatorUseLogfile"
        >
          Logs into logfile
        </label>
        <br />
        <input
          id="emulatorSaveScreenshots"
          type="checkbox"
          checked={emulators.screenshotMode}
          onChange={(e) =>
            setEmulators({ ...emulators, screenshotMode: e.target.checked })
          }
        />
        <label
          className="underlined"
          title="No square in top right corner. Screenshots are saved under `logs/screens`. NOTE: - does not work for T1 - the first screen does contain the square, no way to change it."
          htmlFor="emulatorSaveScreenshots"
        >
          Screenshot mode
        </label>
        <br />
      </div>

      <hr />

      <div>
        <input
          type="text"
          placeholder="Full emulator URL. Do not forget to specify correct model"
          style={{ width: '40%' }}
          value={emulatorUrl.url}
          onChange={(e) => setEmulatorUrl({ ...emulatorUrl, url: e.target.value })}
        />
        <select
          value={emulatorUrl.model}
          onChange={(e) => setEmulatorUrl({ ...emulatorUrl, model: e.target.value })}
        >
          {Object.entries(emulators.versions).map(([model, details]) => (
            <option value={model} key={model}>
              {details.header}
            </option>
          ))}
        </select>
        <button className="positive" onClick={onStartFromUrl}>
          Start from URL
        </button>
      </div>

      <div>
        <input
          type="text"
          placeholder="Firmware branch. Do not forget to specify correct model"
          style={{ width: '30%' }}
          value={emulatorBranch.branch}
          onChange={(e) =>
            setEmulatorBranch({ ...emulatorBranch, branch: e.target.value })
          }
        />
        <select
          value={emulatorBranch.model}
          onChange={(e) =>
            setEmulatorBranch({ ...emulatorBranch, model: e.target.value })
          }
        >
          {Object.entries(emulators.versions).map(([model, details]) => (
            <option value={model} key={model}>
              {details.header}
            </option>
          ))}
        </select>
        <input
          id="emulatorBtcOnly"
          type="checkbox"
          checked={emulatorBranch.btcOnly}
          onChange={(e) =>
            setEmulatorBranch({ ...emulatorBranch, btcOnly: e.target.checked })
          }
        />
        <label
          className="underlined"
          title="Use BTC-only version of the emulator."
          htmlFor="emulatorBtcOnly"
        >
          BTC-only
        </label>
        <button className="positive" onClick={onStartFromBranch}>
          Start from branch
        </button>
      </div>

      {emulatorDownloadMessage && (
        <div className="user-info">{emulatorDownloadMessage}</div>
      )}

      <hr />

      <button className="negative" onClick={onStop}>
        Stop
      </button>
    </section>
  );
};
