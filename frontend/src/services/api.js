import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) =>
    api.post('/api/auth/login', { email, password }),
  
  register: (userData) =>
    api.post('/api/auth/register', userData),
  
  getProfile: (token) =>
    api.get('/api/user/profile', {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// Products API
export const productsAPI = {
  getProducts: (params = {}) =>
    api.get('/api/products', { params }),
  
  getProduct: (id) =>
    api.get(`/api/products/${id}`),
  
  createProduct: (token, productData) =>
    api.post('/api/products', productData, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  updateProduct: (token, id, productData) =>
    api.put(`/api/products/${id}`, productData, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  deleteProduct: (token, id) =>
    api.delete(`/api/products/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  getCategories: () =>
    api.get('/api/categories'),
};

// Cart API
export const cartAPI = {
  getCart: (token) =>
    api.get('/api/cart', {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  addToCart: (token, productId, quantity) =>
    api.post('/api/cart/add', { product_id: productId, quantity }, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  updateCartItem: (token, productId, quantity) =>
    api.put('/api/cart/update', { product_id: productId, quantity }, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  removeFromCart: (token, productId) =>
    api.delete(`/api/cart/remove/${productId}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  clearCart: (token) =>
    api.delete('/api/cart/clear', {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// Orders API
export const ordersAPI = {
  getOrders: (token) =>
    api.get('/api/orders', {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  getOrder: (token, orderId) =>
    api.get(`/api/orders/${orderId}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  createOrder: (token, orderData) =>
    api.post('/api/orders', orderData, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  updateOrderStatus: (token, orderId, status) =>
    api.put(`/api/orders/${orderId}/status`, { status }, {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// Reviews API
export const reviewsAPI = {
  getProductReviews: (productId) =>
    api.get(`/api/products/${productId}/reviews`),
  
  createReview: (token, reviewData) =>
    api.post('/api/reviews', reviewData, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  updateReview: (token, reviewId, reviewData) =>
    api.put(`/api/reviews/${reviewId}`, reviewData, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  deleteReview: (token, reviewId) =>
    api.delete(`/api/reviews/${reviewId}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// Wishlist API
export const wishlistAPI = {
  getWishlist: (token) =>
    api.get('/api/wishlist', {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  addToWishlist: (token, productId) =>
    api.post('/api/wishlist/add', { product_id: productId }, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  removeFromWishlist: (token, productId) =>
    api.delete(`/api/wishlist/remove/${productId}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  isInWishlist: (token, productId) =>
    api.get(`/api/wishlist/check/${productId}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// Analytics API
export const analyticsAPI = {
  getDashboardStats: (token) =>
    api.get('/api/analytics/dashboard', {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  getSalesData: (token, params = {}) =>
    api.get('/api/analytics/sales', {
      params,
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  getTopProducts: (token, params = {}) =>
    api.get('/api/analytics/top-products', {
      params,
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  getUserActivity: (token, params = {}) =>
    api.get('/api/analytics/user-activity', {
      params,
      headers: { Authorization: `Bearer ${token}` },
    }),
};

// Payment API
export const paymentAPI = {
  createPaymentIntent: (token, amount) =>
    api.post('/api/payment/create-intent', { amount }, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  confirmPayment: (token, paymentIntentId) =>
    api.post('/api/payment/confirm', { payment_intent_id: paymentIntentId }, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  
  getPaymentHistory: (token) =>
    api.get('/api/payment/history', {
      headers: { Authorization: `Bearer ${token}` },
    }),
};

export default api;