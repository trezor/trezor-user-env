import { useState, useCallback, useRef } from 'react';

const WEBSOCKET_URL = 'ws://localhost:9001/';
const BACKGROUND_CHECK_PERIOD_MS = 500;

interface LogEvent {
  text: string;
  color: string;
}

interface WebSocketMessage {
  id?: number;
  [key: string]: unknown;
}

export const useWebSocket = () => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const reqIdRef = useRef(0);

  const logEvent = useCallback((text: string, color: string = 'black') => {
    const now = new Date();
    const hours = ('0' + now.getHours()).slice(-2);
    const minutes = ('0' + now.getMinutes()).slice(-2);
    const seconds = ('0' + now.getSeconds()).slice(-2);
    const timestamp = `${hours}:${minutes}:${seconds}`;
    
    setLogs(prev => [{
      text: `${timestamp} - ${text}`,
      color
    }, ...prev]);
  }, []);

  const setupWebSocket = useCallback(() => {
    const websocket = new WebSocket(WEBSOCKET_URL);

    websocket.onopen = () => {
      logEvent('WebSocket connection opened', 'green');
      setWs(websocket);
    };

    websocket.onerror = () => {
      logEvent(
        'WebSocket connection Error',
        'red'
      );
    };

    websocket.onclose = () => {
      logEvent(
        'WebSocket connection closed',
        'red'
      );
      setWs(null);
    };

    return websocket;
  }, [logEvent]);

  const sendMessage = useCallback((msg: WebSocketMessage) => {
    if (isWaitingForResponse) {
      logEvent('Waiting for response, please wait...', 'red');
      return;
    }

    if (!msg) {
      return { error: 'Please enter a message' };
    }

    if (!ws || ws.readyState !== WebSocket.OPEN) {
      logEvent('WebSocket not connected', 'red');
      return { error: 'WebSocket not connected - trying to connect...' };
    }

    logEvent(`Request sent: ${JSON.stringify(msg)}`, 'blue');

    const requestToSend = JSON.stringify({
      ...msg,
      id: reqIdRef.current
    });
    
    ws.send(requestToSend);
    reqIdRef.current++;
    setIsWaitingForResponse(true);
  }, [ws, isWaitingForResponse, logEvent]);

  const sendMessageOnBackground = useCallback((json: WebSocketMessage) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(json));
    }
  }, [ws]);

  const closeWebsocket = useCallback(() => {
    if (ws) {
      ws.close();
    }
  }, [ws]);

  return {
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
  };
};
