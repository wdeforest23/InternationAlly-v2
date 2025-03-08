class ApiService {
  static async login(email, password) {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    localStorage.setItem('token', data.token);
    return data;
  }

  static async signup(userData) {
    const response = await fetch('/api/signup', {
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
      const response = await fetch('/api/profile', {
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
      const response = await fetch('/api/profile', {
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
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          throw new Error('Session expired. Please login again.');
        }
        const data = await response.json();
        throw new Error(data.error || 'Failed to send message');
      }

      const data = await response.json();
      console.log('API response:', data); // Debug log
      return data;
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  }
}

export default ApiService; 