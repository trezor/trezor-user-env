export interface BridgeState {
  versions: string[];
  selected: string;
  outputToLogfile: boolean;
  status: string;
  statusColor: string;
  hasSuiteLocal: boolean;
}

export interface TropicState {
  outputToLogfile: boolean;
  status: string;
  statusColor: string;
}

export interface EmulatorVersions {
  header: string;
  versions: string[];
  selected: string;
}

export interface EmulatorsState {
  versions: {
    [key: string]: EmulatorVersions;
  };
  wipeDevice: boolean;
  screenshotMode: boolean;
  animations: boolean;
  outputToLogfile: boolean;
  status: string;
  statusColor: string;
}

export interface EmulatorUrlState {
  url: string;
  model: string;
}

export interface EmulatorBranchState {
  branch: string;
  model: string;
  btcOnly: boolean;
}

export interface EmulatorCommandsState {
  seed: string;
  shamirShares: number;
  shamirThreshold: number;
}

export interface RegtestState {
  status: string;
  statusColor: string;
  mineBlocks: number;
  mineAddress: string;
  sendAmount: number;
  sendAddress: string;
}

export interface ServerState {
  command: string;
}

export interface NotificationState {
  showPopup: boolean;
  text: string;
  header: string;
  isError: boolean;
}

export interface BackgroundCheckData {
  [key: string]: unknown;
  bridge_status?: BridgeStatus;
  emulator_status?: Status;
  tropic_status?: Status;
  regtest_status?: boolean;
}

export interface BridgeStatus {
  is_running: boolean;
  version?: string;
}

export interface Status {
  is_running: boolean;
  version?: string;
}

export interface ClientResponseData {
  type: string;
  firmwares: {
    [key: string]: string[];
  };
  bridges: string[];
}

export interface ServerResponse {
  success?: boolean;
  response?: string;
  type?: string;
  [key: string]: unknown;
}
