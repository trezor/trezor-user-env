import React from 'react';
import { RegtestState } from '../types';

interface RegtestSectionProps {
  regtest: RegtestState;
  setRegtest: (regtest: RegtestState) => void;
  onMine: () => void;
  onSend: () => void;
}

export const RegtestSection: React.FC<RegtestSectionProps> = ({
  regtest,
  setRegtest,
  onMine,
  onSend
}) => {
  return (
    <section>
      <h3>Regtest</h3>

      <div style={{ color: regtest.statusColor }}>
        <b>
          Status: <span>{regtest.status}</span>
        </b>
      </div>

      <label htmlFor="regtest-mine-blocks">Blocks</label>
      <input
        id="regtest-mine-blocks"
        type="number"
        size={5}
        min={1}
        max={10000}
        value={regtest.mineBlocks}
        onChange={(e) =>
          setRegtest({ ...regtest, mineBlocks: parseInt(e.target.value) })
        }
      />
      <br />
      <label htmlFor="regtest-mine-address">Optional address of a miner</label>
      <input
        id="regtest-mine-address"
        size={62}
        value={regtest.mineAddress}
        onChange={(e) =>
          setRegtest({ ...regtest, mineAddress: e.target.value })
        }
      />
      <br />
      <button onClick={onMine}>Mine regtest block(s)</button>

      <hr />

      <label htmlFor="regtest-send-amount">BTC amount</label>
      <input
        id="regtest-send-amount"
        type="number"
        size={10}
        step="any"
        value={regtest.sendAmount}
        onChange={(e) =>
          setRegtest({ ...regtest, sendAmount: parseFloat(e.target.value) })
        }
      />
      <br />
      <label htmlFor="regtest-send-address">Regtest address</label>
      <input
        id="regtest-send-address"
        size={62}
        value={regtest.sendAddress}
        onChange={(e) =>
          setRegtest({ ...regtest, sendAddress: e.target.value })
        }
      />
      <br />
      <button onClick={onSend}>Send regtest BTC to address</button>
    </section>
  );
};
