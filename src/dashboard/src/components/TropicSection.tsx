import React from 'react';
import { TropicState } from '../types';

interface TropicSectionProps {
  tropic: TropicState;
  setTropic: (tropic: TropicState) => void;
  onStart: () => void;
  onStop: () => void;
}

export const TropicSection: React.FC<TropicSectionProps> = ({
  tropic,
  setTropic,
  onStart,
  onStop
}) => {
  return (
    <section>
      <h3>Tropic Square Model Server</h3>
      <div>
        <i>Control Tropic Square model server (required for T3W1 emulator).</i>
        <br />
        <button className="positive" onClick={onStart}>
          Start
        </button>
        <button className="negative" onClick={onStop}>
          Stop
        </button>
        <input
          id="tropicUseLogfile"
          type="checkbox"
          checked={tropic.outputToLogfile}
          onChange={(e) =>
            setTropic({ ...tropic, outputToLogfile: e.target.checked })
          }
        />
        <label
          className="underlined"
          title="Save tropic model logs into logfile. Otherwise, logs are shown in console."
          htmlFor="tropicUseLogfile"
        >
          Logs into logfile
        </label>
        <br />
      </div>
      <div>
        <div style={{ color: tropic.statusColor }}>
          <b>
            Status: <span>{tropic.status}</span>
          </b>
        </div>
        <div className="explain-note">
          The Tropic Square model server is automatically started when launching
          a T3W1 emulator, but can also be controlled manually here.
        </div>
      </div>
    </section>
  );
};
