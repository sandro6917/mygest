import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { 
  DashboardIcon, 
  PraticheIcon, 
  DocumentiIcon, 
  AnagraficheIcon,
  CalendarIcon,
  UserIcon,
  LogoutIcon,
  ThemeIcon
} from '@/components/icons/Icons';

const getInitialTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') {
    return 'light';
  }
  const savedTheme = window.localStorage.getItem('theme') as 'light' | 'dark' | null;
  const initialTheme = savedTheme ?? 'light';
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', initialTheme);
  }
  return initialTheme;
};

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<'light' | 'dark'>(getInitialTheme);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">
            <DashboardIcon size={32} />
          </span>
          <span className="brand-name">MyGest</span>
        </Link>

        {isAuthenticated && (
          <>
            <div className="navbar-menu">
              <Link to="/" className="nav-link">
                <DashboardIcon size={20} />
                <span>Dashboard</span>
              </Link>
              <Link to="/pratiche" className="nav-link">
                <PraticheIcon size={20} />
                <span>Pratiche</span>
              </Link>
              <Link to="/fascicoli" className="nav-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                </svg>
                <span>Fascicoli</span>
              </Link>
              <Link to="/documenti" className="nav-link">
                <DocumentiIcon size={20} />
                <span>Documenti</span>
              </Link>
              <Link to="/anagrafiche" className="nav-link">
                <AnagraficheIcon size={20} />
                <span>Anagrafiche</span>
              </Link>
              <Link to="/scadenze" className="nav-link">
                <CalendarIcon size={20} />
                <span>Scadenze</span>
              </Link>
              <Link to="/comunicazioni" className="nav-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <span>Comunicazioni</span>
              </Link>
              <Link to="/archivio" className="nav-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="7" rx="2"></rect>
                  <rect x="3" y="14" width="18" height="7" rx="2"></rect>
                  <line x1="9" y1="6.5" x2="9" y2="6.51"></line>
                  <line x1="9" y1="17.5" x2="9" y2="17.51"></line>
                </svg>
                <span>Archivio</span>
              </Link>
              <Link to="/archivio-fisico/operazioni" className="nav-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="3" width="20" height="5" rx="2"></rect>
                  <rect x="2" y="10" width="20" height="5" rx="2"></rect>
                  <rect x="2" y="17" width="20" height="5" rx="2"></rect>
                </svg>
                <span>Operazioni</span>
              </Link>
              <Link to="/help" className="nav-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <span>Help</span>
              </Link>
              <Link to="/ai-classifier/jobs" className="nav-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                  <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                  <line x1="6" y1="6" x2="6.01" y2="6"></line>
                  <line x1="6" y1="18" x2="6.01" y2="18"></line>
                </svg>
                <span>AI Classifier</span>
              </Link>
            </div>

            <div className="navbar-right">
              <button
                onClick={toggleTheme}
                className="btn-icon"
                title={theme === 'light' ? 'Modalità scura' : 'Modalità chiara'}
              >
                <ThemeIcon size={20} />
              </button>

              <div className="user-menu">
                <UserIcon size={18} />
                <span className="user-name">
                  {user?.first_name || user?.username}
                </span>
                <button onClick={handleLogout} className="btn-icon-text">
                  <LogoutIcon size={18} />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </nav>
  );
}
