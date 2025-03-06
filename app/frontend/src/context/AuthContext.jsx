import { createContext, useContext, useState, useEffect } from 'react';
import { useUI } from './UIContext';
import ApiService from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const { showError, startLoading, stopLoading } = useUI();

  // Check authentication on page load
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const userData = await ApiService.getProfile();
          setUser(userData);
        } catch (error) {
          console.error('Auth initialization error:', error);
          localStorage.removeItem('token');
        }
      }
      setIsInitialized(true); // Set initialized regardless of outcome
    };

    initializeAuth();
  }, []);

  const login = async (email, password) => {
    startLoading();
    try {
      const data = await ApiService.login(email, password);
      setUser(data.user);
      return true;
    } catch (error) {
      showError('Login failed: ' + (error.message || 'Please try again'));
      return false;
    } finally {
      stopLoading();
    }
  };

  const signup = async (userData) => {
    startLoading();
    try {
      const data = await ApiService.signup(userData);
      setUser(data.user);
      return data;
    } catch (error) {
      showError('Signup failed: ' + (error.message || 'Please try again'));
      throw error;
    } finally {
      stopLoading();
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  // Don't show loading spinner during initialization
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-DEFAULT"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      signup, 
      logout, 
      isInitialized,
      isAuthenticated: !!user 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 