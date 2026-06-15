import { createContext, useContext, useState, useEffect } from 'react';
import { getUser, isLoggedIn, clearAuth, saveAuth } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(getUser());
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  useEffect(() => {
    setUser(getUser());
    setLoggedIn(isLoggedIn());
  }, []);

  const login = (data) => {
    saveAuth(data);
    setUser(getUser());
    setLoggedIn(true);
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    setLoggedIn(false);
  };

  return (
    <AuthContext.Provider value={{ user, loggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);