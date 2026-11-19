import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from './api.js';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const fetchUser = useCallback(async () => {
    try {
      return await api.getMe();
    } catch (error) {
      if (error.status === 401) localStorage.removeItem('token');
      return null;
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUser().then(u => {
        setUser(u);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [fetchUser]);

  const login = async (email, password) => {
    const result = await api.login({ email, password });
    localStorage.setItem('token', result.access_token);
    setUser(result.user);
    return result.user;
  };

  const register = async (data) => {
    const result = await api.register(data);
    localStorage.setItem('token', result.access_token);
    setUser(result.user);
    return result.user;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/login', { replace: true });
  };

  const value = { user, loading, login, register, logout };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}