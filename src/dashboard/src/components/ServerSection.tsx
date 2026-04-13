import React from 'react';
import { ServerState } from '../types';

interface ServerSectionProps {
  server: ServerState;
  setServer: (server: ServerState) => void;
  onSendCommand: () => void;
  onPing: () => void;
  onExit: () => void;
  onCloseWebsocket: () => void;
}

export const ServerSection: React.FC<ServerSectionProps> = ({
  server,
  setServer,
  onSendCommand,
  onPing,
  onExit,
  onCloseWebsocket
}) => {
  return (
    <section>
      <h3>Server</h3>
      <textarea
        id="server-input"
        rows={3}
        value={server.command}
        onChange={(e) => setServer({ ...server, command: e.target.value })}
      />
      <br />
      <button onClick={onSendCommand}>Send JSON</button>
      <hr />
      <button onClick={onPing}>Ping server</button>
      <button onClick={onExit}>Exit server</button>
      <button onClick={onCloseWebsocket}>Close websocket</button>
    </section>
  );
};
