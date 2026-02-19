import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    try {
      await login({ username, password });
      navigate('/');
    } catch (err) {
      // Error handled by store
      console.error('Login failed:', err);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🔐 MyGest Login</h1>
          <p>Accedi al tuo gestionale</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Inserisci username"
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Inserisci password"
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            className="btn-primary btn-block"
            disabled={isLoading}
          >
            {isLoading ? 'Accesso in corso...' : 'Accedi'}
          </button>
        </form>

        <div className="login-footer">
          <p className="text-sm text-gray-600">
            MyGest v1.5.0 - © 2025
          </p>
        </div>
      </div>
    </div>
  );
}
