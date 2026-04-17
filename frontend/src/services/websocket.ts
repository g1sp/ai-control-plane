/**
 * WebSocket client for real-time metrics streaming.
 * Handles connection lifecycle, reconnection, and fallback strategies.
 */

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export interface MetricsEvent {
  type: string;
  timestamp: string;
  data: Record<string, any>;
}

export type EventHandler = (event: MetricsEvent) => void;

export class WebSocketClient {
  private url: string;
  private ws: WebSocket | null = null;
  private eventSource: EventSource | null = null;
  private usingSSE = false;
  private usingPolling = false;
  private pollInterval: NodeJS.Timeout | null = null;

  private state: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 16000;

  private heartbeatTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageBuffer: string[] = [];
  private bufferSize = 100;

  private handlers: Map<string, Set<EventHandler>> = new Map();
  private stateChangeHandlers: Set<(state: ConnectionState) => void> = new Set();

  constructor(url: string) {
    this.url = url;
  }

  async connect(): Promise<void> {
    if (this.state === 'connected' || this.state === 'connecting') {
      return;
    }

    this.setState('connecting');

    try {
      await this.tryWebSocket();
    } catch (error) {
      console.warn('WebSocket failed, trying SSE:', error);
      try {
        await this.trySSE();
      } catch (sseError) {
        console.warn('SSE failed, falling back to polling:', sseError);
        this.usePolling();
      }
    }
  }

  private tryWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.usingSSE = false;
        this.usingPolling = false;

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.setState('connected');
          this.startHeartbeat();
          this.flushMessageBuffer();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.setState('error');
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket closed');
          this.stopHeartbeat();
          this.ws = null;
          if (this.state === 'connected') {
            this.reconnect();
          }
        };

        // Timeout for connection attempt
        setTimeout(() => {
          if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000);
      } catch (error) {
        reject(error);
      }
    });
  }

  private trySSE(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const sseUrl = this.url.replace(/^wss?/, 'https').replace(/^ws/, 'http') + '?use_sse=true';
        this.eventSource = new EventSource(sseUrl);
        this.usingSSE = true;
        this.usingPolling = false;

        this.eventSource.onopen = () => {
          console.log('SSE connected');
          this.reconnectAttempts = 0;
          this.setState('connected');
          this.flushMessageBuffer();
          resolve();
        };

        this.eventSource.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.eventSource.onerror = (error) => {
          console.error('SSE error:', error);
          if (this.eventSource?.readyState === EventSource.CLOSED) {
            this.eventSource.close();
            this.eventSource = null;
            this.setState('error');
            reject(error);
          }
        };

        setTimeout(() => {
          if (this.eventSource && this.eventSource.readyState === EventSource.CONNECTING) {
            this.eventSource.close();
            reject(new Error('SSE connection timeout'));
          }
        }, 5000);
      } catch (error) {
        reject(error);
      }
    });
  }

  private usePolling(): void {
    console.log('Falling back to HTTP polling');
    this.usingPolling = true;
    this.setState('connected');
    this.reconnectAttempts = 0;

    this.pollInterval = setInterval(async () => {
      try {
        const response = await fetch(this.url.replace(/^wss?/, 'https').replace(/^ws/, 'http'));
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data)) {
            data.forEach(event => this.handleMessage(JSON.stringify(event)));
          } else {
            this.handleMessage(JSON.stringify(data));
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 5000);
  }

  private handleMessage(data: string): void {
    try {
      const event: MetricsEvent = JSON.parse(data);
      this.resetHeartbeatTimeout();
      this.emit(event.type, event);
    } catch (error) {
      console.error('Failed to parse message:', error, data);
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
        this.resetHeartbeatTimeout();
      }
    }, 30000);

    this.resetHeartbeatTimeout();
  }

  private resetHeartbeatTimeout(): void {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
    }

    this.heartbeatTimeout = setTimeout(() => {
      if (this.ws) {
        console.warn('Heartbeat timeout, reconnecting');
        this.ws.close();
      }
    }, 60000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.setState('error');
      return;
    }

    this.setState('reconnecting');
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts) + Math.random() * 1000,
      this.maxReconnectDelay
    );

    console.log(`Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts + 1})`);
    this.reconnectAttempts++;

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private flushMessageBuffer(): void {
    if (this.usingPolling || this.usingSSE) {
      this.messageBuffer = [];
      return;
    }

    while (this.messageBuffer.length > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = this.messageBuffer.shift();
      if (message) {
        this.ws.send(message);
      }
    }
  }

  private setState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.stateChangeHandlers.forEach(handler => handler(newState));
    }
  }

  subscribe(eventType: string, handler: EventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }

    const handlers = this.handlers.get(eventType)!;
    handlers.add(handler);

    return () => {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.handlers.delete(eventType);
      }
    };
  }

  on(eventType: string, handler: EventHandler): () => void {
    return this.subscribe(eventType, handler);
  }

  onStateChange(handler: (state: ConnectionState) => void): () => void {
    this.stateChangeHandlers.add(handler);
    return () => {
      this.stateChangeHandlers.delete(handler);
    };
  }

  private emit(eventType: string, event: MetricsEvent): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => handler(event));
    }

    const allHandlers = this.handlers.get('*');
    if (allHandlers) {
      allHandlers.forEach(handler => handler(event));
    }
  }

  send(message: any): void {
    const data = JSON.stringify(message);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else if (this.usingPolling || this.usingSSE) {
      // Can't send with SSE/polling, just buffer for later
      if (this.messageBuffer.length < this.bufferSize) {
        this.messageBuffer.push(data);
      }
    } else {
      // Buffer for when connection is established
      if (this.messageBuffer.length < this.bufferSize) {
        this.messageBuffer.push(data);
      }
    }
  }

  getState(): ConnectionState {
    return this.state;
  }

  isConnected(): boolean {
    return this.state === 'connected';
  }

  disconnect(): void {
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }

    this.messageBuffer = [];
    this.setState('disconnected');
  }
}
