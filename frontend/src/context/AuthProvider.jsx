import { useEffect, useState } from 'react';

import {
  authStorage,
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  signup as signupRequest,
} from '../lib/api';
import { AuthContext } from './authContext';


export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(authStorage.getStoredToken()));

  useEffect(() => {
    let isMounted = true;

    async function loadUser() {
      if (!authStorage.getStoredToken()) {
        setIsLoading(false);
        return;
      }

      try {
        const data = await getCurrentUser();
        if (isMounted) {
          setUser(data.user);
        }
      } catch {
        authStorage.clearToken();
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadUser();

    return () => {
      isMounted = false;
    };
  }, []);

  async function login(credentials) {
    const data = await loginRequest(credentials);
    authStorage.saveToken(data.token);
    setUser(data.user);
    return data.user;
  }

  async function signup(account) {
    const data = await signupRequest(account);
    authStorage.saveToken(data.token);
    setUser(data.user);
    return data.user;
  }

  async function logout() {
    try {
      await logoutRequest();
    } finally {
      authStorage.clearToken();
      setUser(null);
    }
  }

  const value = {
    user,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    signup,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
