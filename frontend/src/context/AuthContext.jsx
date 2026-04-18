import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { authAPI } from '../lib/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('promanage_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  // Verify token on mount
  useEffect(() => {
    const token = localStorage.getItem('promanage_token');
    if (token && user) {
      authAPI.me().then(res => {
        setUser(res.data);
        localStorage.setItem('promanage_user', JSON.stringify(res.data));
      }).catch(() => {
        setUser(null);
        localStorage.removeItem('promanage_user');
        localStorage.removeItem('promanage_token');
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (identifier, password) => {
    setLoading(true);
    try {
      const res = await authAPI.login(identifier, password);
      const { user: userData, token } = res.data;
      setUser(userData);
      localStorage.setItem('promanage_user', JSON.stringify(userData));
      localStorage.setItem('promanage_token', token);
      setLoading(false);
      return { success: true };
    } catch (err) {
      setLoading(false);
      return { success: false, error: err.response?.data?.detail || 'Gagal masuk' };
    }
  }, []);

  const register = useCallback(async (data) => {
    setLoading(true);
    try {
      const res = await authAPI.register(data);
      const { user: userData, token } = res.data;
      setUser(userData);
      localStorage.setItem('promanage_user', JSON.stringify(userData));
      localStorage.setItem('promanage_token', token);
      setLoading(false);
      return { success: true };
    } catch (err) {
      setLoading(false);
      return { success: false, error: err.response?.data?.detail || 'Gagal mendaftar' };
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('promanage_user');
    localStorage.removeItem('promanage_token');
  }, []);

  const updateProfile = useCallback((updates) => {
    setUser(prev => {
      const updated = { ...prev, ...updates };
      localStorage.setItem('promanage_user', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const canManage = user?.role === 'Manager' || user?.role === 'Admin';
  const isTeamLead = user?.role === 'Team Lead';
  const isMember = user?.role === 'Anggota Tim';

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      updateProfile,
      canManage,
      isTeamLead,
      isMember,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
