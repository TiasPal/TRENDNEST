import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import { wishlistAPI } from '../services/api';
import { useCart } from '../contexts/CartContext';
import LoadingSpinner from '../components/common/LoadingSpinner';

const Wishlist = () => {
  const { addToCart } = useCart();
  
  const { data: wishlistData, isLoading } = useQuery(
    ['wishlist'],
    () => wishlistAPI.getWishlist(localStorage.getItem('token'))
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const wishlistItems = wishlistData?.data?.items || [];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Wishlist</h1>
        
        {wishlistItems.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg mb-4">Your wishlist is empty</p>
            <Link to="/products" className="btn-primary">
              Browse Products
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {wishlistItems.map((item) => (
              <div key={item.product._id} className="product-card">
                <div className="aspect-w-1 aspect-h-1 w-full overflow-hidden rounded-t-xl">
                  <Link to={`/products/${item.product._id}`}>
                    {item.product.image_base64 ? (
                      <img
                        src={`data:image/jpeg;base64,${item.product.image_base64}`}
                        alt={item.product.name}
                        className="h-48 w-full object-cover hover:scale-105 transition-transform duration-200"
                      />
                    ) : (
                      <div className="h-48 w-full bg-gray-200 flex items-center justify-center">
                        <span className="text-gray-500">No Image</span>
                      </div>
                    )}
                  </Link>
                </div>
                <div className="p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    <Link to={`/products/${item.product._id}`} className="hover:text-primary-600">
                      {item.product.name}
                    </Link>
                  </h3>
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {item.product.description}
                  </p>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xl font-bold text-primary-600">
                      ${item.product.price}
                    </span>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => addToCart(item.product._id, 1)}
                      className="flex-1 btn-primary"
                      disabled={item.product.stock === 0}
                    >
                      {item.product.stock === 0 ? 'Out of Stock' : 'Add to Cart'}
                    </button>
                    <Link
                      to={`/products/${item.product._id}`}
                      className="flex-1 btn-outline text-center"
                    >
                      View
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Wishlist;