// Authentication utility functions

const API_BASE = '';

// Check if user is authenticated
function isAuthenticated() {
    return !!localStorage.getItem('token');
}

// Get auth token
function getToken() {
    return localStorage.getItem('token');
}

// Get username
function getUsername() {
    return localStorage.getItem('username');
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = '/login';
}

// Make authenticated API request
async function apiRequest(url, options = {}) {
    const token = getToken();
    
    if (!token) {
        logout();
        return;
    }
    
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };
    
    try {
        const response = await fetch(API_BASE + url, {
            ...options,
            headers
        });
        
        // If unauthorized, logout
        if (response.status === 401) {
            logout();
            return;
        }
        
        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Verify token on page load
async function verifyToken() {
    if (!isAuthenticated()) {
        return false;
    }
    
    try {
        const response = await apiRequest('/api/auth/verify');
        return response && response.ok;
    } catch (error) {
        return false;
    }
}

// Protect page (redirect to login if not authenticated)
async function protectPage() {
    const valid = await verifyToken();
    
    if (!valid) {
        window.location.href = '/login';
    }
}
