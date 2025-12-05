import React from 'react';
import { BridgeState } from '../types';

interface BridgeSectionProps {
  bridges: BridgeState;
  setBridges: (bridges: BridgeState) => void;
  onStart: () => void;
  onStop: () => void;
}

export const BridgeSection: React.FC<BridgeSectionProps> = ({
  bridges,
  setBridges,
  onStart,
  onStop
}) => {
  return (
    <section>
      <h3>Bridge</h3>
      <div>
        <i>Start Bridge with emulator support.</i>
        <br />
        <select
          value={bridges.selected}
          onChange={(e) => setBridges({ ...bridges, selected: e.target.value })}
        >
          {bridges.versions.map((version) => (
            <option key={version} value={version}>
              {version}
            </option>
          ))}
        </select>
        <button className="positive" onClick={onStart}>
          Start
        </button>
        <button className="negative" onClick={onStop}>
          Stop
        </button>
        <input
          id="bridgeUseLogfile"
          type="checkbox"
          checked={bridges.outputToLogfile}
          onChange={(e) =>
            setBridges({ ...bridges, outputToLogfile: e.target.checked })
          }
        />
        <label
          className="underlined"
          title="Save bridge logs into logfile. Otherwise, logs are shown in console."
          htmlFor="bridgeUseLogfile"
        >
          Logs into logfile
        </label>
        <br />
      </div>
      <div>
        <div style={{ color: bridges.statusColor }}>
          <b>
            Status: <span>{bridges.status}</span>
          </b>
        </div>
        <div className="explain-note">
          You may also check bridge status page on{' '}
          <a href="http://0.0.0.0:21325/status/" target="_blank" rel="noreferrer">
            http://0.0.0.0:21325/status/
          </a>{' '}
          when the bridge is running
          {bridges.hasSuiteLocal ? (
            <div style={{ color: 'green' }}>
              You have mounted local Suite - local node bridge is available.
            </div>
          ) : (
            <div>
              Local Suite is not mounted - if needed, run `ln -s
              [local-suite-path] trezor-suite` in root dir and restart server.
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
