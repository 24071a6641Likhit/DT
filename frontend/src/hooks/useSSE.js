import { useState, useEffect, useRef } from 'react';
import { createSSEConnection } from '../services/api';

export const useSSE = () => {
  const [liveData, setLiveData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    const handleMessage = (type, data) => {
      if (type === 'readings') {
        setLiveData(data);
      } else if (type === 'alert') {
        setAlerts((prev) => [data, ...prev].slice(0, 10));
      }
    };

    const handleError = (error) => {
      console.error('SSE error:', error);
      setIsConnected(false);
    };

    eventSourceRef.current = createSSEConnection(handleMessage, handleError);
    
    eventSourceRef.current.onopen = () => {
      setIsConnected(true);
      console.log('SSE connected');
    };

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        setIsConnected(false);
      }
    };
  }, []);

  return { liveData, alerts, isConnected };
};
