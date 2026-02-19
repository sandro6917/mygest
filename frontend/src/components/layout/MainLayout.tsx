import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export function MainLayout() {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="footer">
        <p>© 2025 MyGest - v1.5.0</p>
      </footer>
    </div>
  );
}
