import React, { createContext, useContext, useState, useEffect } from 'react';
import { cartAPI } from '../services/api';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [cart, setCart] = useState({ items: [], total_amount: 0 });
  const [loading, setLoading] = useState(false);
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    if (isAuthenticated && token) {
      fetchCart();
    } else {
      setCart({ items: [], total_amount: 0 });
      setCartCount(0);
    }
  }, [isAuthenticated, token]);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const response = await cartAPI.getCart(token);
      setCart(response.data);
      setCartCount(response.data.items.reduce((total, item) => total + item.quantity, 0));
    } catch (error) {
      console.error('Error fetching cart:', error);
      toast.error('Failed to load cart');
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    if (!isAuthenticated) {
      toast.error('Please login to add items to cart');
      return false;
    }

    try {
      setLoading(true);
      await cartAPI.addToCart(token, productId, quantity);
      await fetchCart();
      toast.success('Item added to cart');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to add item to cart';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const updateCartItem = async (productId, quantity) => {
    if (!isAuthenticated) {
      toast.error('Please login to update cart');
      return false;
    }

    try {
      setLoading(true);
      await cartAPI.updateCartItem(token, productId, quantity);
      await fetchCart();
      toast.success('Cart updated');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to update cart';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (productId) => {
    if (!isAuthenticated) {
      toast.error('Please login to remove items from cart');
      return false;
    }

    try {
      setLoading(true);
      await cartAPI.removeFromCart(token, productId);
      await fetchCart();
      toast.success('Item removed from cart');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to remove item from cart';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const clearCart = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to clear cart');
      return false;
    }

    try {
      setLoading(true);
      await cartAPI.clearCart(token);
      await fetchCart();
      toast.success('Cart cleared');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to clear cart';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    cart,
    cartCount,
    loading,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: fetchCart,
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};