import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import Billing from './pages/Billing';
import './App.css';

function Navigation() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav style={styles.nav}>
      <div style={styles.navContainer}>
        <h1 style={styles.title}>⚡ Energy Monitor</h1>
        <div style={styles.navLinks}>
          <Link 
            to="/" 
            style={{...styles.navLink, ...(isActive('/') ? styles.navLinkActive : {})}}
          >
            Dashboard
          </Link>
          <Link 
            to="/alerts" 
            style={{...styles.navLink, ...(isActive('/alerts') ? styles.navLinkActive : {})}}
          >
            Alerts
          </Link>
          <Link 
            to="/billing" 
            style={{...styles.navLink, ...(isActive('/billing') ? styles.navLinkActive : {})}}
          >
            Billing
          </Link>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div style={styles.app}>
        <Navigation />
        <main style={styles.main}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/billing" element={<Billing />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

const styles = {
  app: {
    minHeight: '100vh',
    backgroundColor: '#f5f6fa'
  },
  nav: {
    backgroundColor: '#2c3e50',
    color: 'white',
    padding: '15px 0',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  navContainer: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: 'bold'
  },
  navLinks: {
    display: 'flex',
    gap: '20px'
  },
  navLink: {
    color: 'white',
    textDecoration: 'none',
    padding: '8px 16px',
    borderRadius: '4px',
    transition: 'background-color 0.2s'
  },
  navLinkActive: {
    backgroundColor: '#34495e'
  },
  main: {
    padding: '20px 0'
  }
};

export default App;
