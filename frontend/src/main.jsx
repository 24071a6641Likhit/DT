import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// In dev mode, attempt to unregister any service workers and clear caches
// This helps avoid stale service workers from previous projects controlling the dev origin/port
if (import.meta.env.DEV && typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
  ;(async () => {
    try {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map(r => r.unregister().catch(() => {})));
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
      console.info(`Dev: unregistered ${regs.length} service workers and cleared ${keys.length} caches`);
    } catch (e) {
      console.warn('Dev: failed to unregister service workers', e);
    }
  })();
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
