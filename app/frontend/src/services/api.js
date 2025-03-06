class ApiService {
  static BASE_URL = 'http://localhost:5000';

  static async login(email, password) {
    const response = await fetch(`${this.BASE_URL}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    // Store the token
    localStorage.setItem('token', data.token);
    return data;
  }

  static async signup(userData) {
    const response = await fetch(`${this.BASE_URL}/api/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Signup failed');
    }
    
    // Store the token
    localStorage.setItem('token', data.token);
    return data;
  }

  static async getProfile() {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    try {
      const response = await fetch(`${this.BASE_URL}/api/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token'); // Clear invalid token
          throw new Error('Session expired. Please login again.');
        }
        const data = await response.json();
        throw new Error(data.error || 'Failed to fetch profile');
      }
      
      return response.json();
    } catch (error) {
      console.error('Profile fetch error:', error);
      throw error;
    }
  }

  static async updateProfile(profileData) {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    try {
      const response = await fetch(`${this.BASE_URL}/api/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          throw new Error('Session expired. Please login again.');
        }
        const data = await response.json();
        throw new Error(data.error || 'Failed to update profile');
      }
      
      return response.json();
    } catch (error) {
      console.error('Profile update error:', error);
      throw error;
    }
  }

  static async sendChatMessage(message) {
    const response = await fetch(`${this.BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    return response.json();
  }
}

export default ApiService; 