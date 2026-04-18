import React, { createContext, useContext, useState, useCallback } from 'react';
import { mockUsers, getUserByEmail } from '../data/mock';

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

  const login = useCallback(async (emailOrPhone, password) => {
    setLoading(true);
    // Mock login - simulate API call
    await new Promise(r => setTimeout(r, 800));
    const found = mockUsers.find(
      u => u.email === emailOrPhone || u.phone === emailOrPhone
    );
    if (found) {
      setUser(found);
      localStorage.setItem('promanage_user', JSON.stringify(found));
      setLoading(false);
      return { success: true };
    }
    setLoading(false);
    return { success: false, error: 'Kredensial tidak valid' };
  }, []);

  const loginWhatsApp = useCallback(async (phone) => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 800));
    const found = mockUsers.find(u => u.phone === phone);
    if (found) {
      setUser(found);
      localStorage.setItem('promanage_user', JSON.stringify(found));
      setLoading(false);
      return { success: true };
    }
    setLoading(false);
    return { success: false, error: 'Nomor WhatsApp tidak terdaftar' };
  }, []);

  const register = useCallback(async (data) => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 800));
    const newUser = {
      id: `usr-${Date.now()}`,
      email: data.email || '',
      name: data.name,
      role: 'Anggota Tim',
      phone: data.phone,
      createdAt: new Date().toISOString(),
      createdBy: null,
      deletedAt: null,
      avatar: null,
    };
    setUser(newUser);
    localStorage.setItem('promanage_user', JSON.stringify(newUser));
    setLoading(false);
    return { success: true };
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('promanage_user');
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
      loginWhatsApp,
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
