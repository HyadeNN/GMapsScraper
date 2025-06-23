import { useState, useEffect, useRef, useCallback } from 'react';

const useWebSocket = (url = 'ws://localhost:8000/api/ws/connect') => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [logs, setLogs] = useState([]);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);
      
      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        
        // Send ping to test connection
        sendMessage({ type: 'ping' });
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);

          // Handle different message types
          switch (message.type) {
            case 'pong':
              console.log('WebSocket ping successful');
              break;
              
            case 'log_message':
              setLogs(prevLogs => {
                const newLogs = [...prevLogs, message.data];
                // Keep only last 100 log entries
                return newLogs.slice(-100);
              });
              break;
              
            case 'progress_update':
              // This will be handled by the progress component via lastMessage
              break;
              
            case 'connection_established':
              console.log('WebSocket connection established:', message.message);
              break;
              
            case 'error':
              console.error('WebSocket error message:', message.message);
              break;
              
            default:
              console.log('Received WebSocket message:', message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          console.log(`Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [url]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.close(1000, 'Manual disconnect');
    }
    
    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket is not connected, cannot send message');
      return false;
    }
  }, []);

  const sendStartScraping = useCallback((operationId, settings, locations) => {
    return sendMessage({
      type: 'start_scraping',
      data: {
        operation_id: operationId,
        settings,
        locations
      }
    });
  }, [sendMessage]);

  const sendPauseScraping = useCallback(() => {
    return sendMessage({ type: 'pause_scraping' });
  }, [sendMessage]);

  const sendResumeScraping = useCallback(() => {
    return sendMessage({ type: 'resume_scraping' });
  }, [sendMessage]);

  const sendStopScraping = useCallback(() => {
    return sendMessage({ type: 'stop_scraping' });
  }, [sendMessage]);

  const sendGetStatus = useCallback(() => {
    return sendMessage({ type: 'get_status' });
  }, [sendMessage]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    connectionStatus,
    logs,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    sendStartScraping,
    sendPauseScraping,
    sendResumeScraping,
    sendStopScraping,
    sendGetStatus,
    clearLogs,
    isConnected: connectionStatus === 'connected'
  };
};

export default useWebSocket;