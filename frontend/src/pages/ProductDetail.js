import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import { productsAPI } from '../services/api';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { StarIcon, HeartIcon, ShareIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const ProductDetail = () => {
  const { id } = useParams();
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);

  const { data: product, isLoading, error } = useQuery(
    ['product', id],
    () => productsAPI.getProduct(id),
    {
      enabled: !!id,
    }
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Product not found
          </h2>
          <Link to="/products" className="btn-primary">
            Back to Products
          </Link>
        </div>
      </div>
    );
  }

  const productData = product.data;

  const handleAddToCart = async () => {
    const success = await addToCart(productData._id, quantity);
    if (success) {
      setQuantity(1);
    }
  };

  const renderStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i}>
          {i <= rating ? (
            <StarIconSolid className="h-5 w-5 text-yellow-400" />
          ) : (
            <StarIcon className="h-5 w-5 text-gray-300" />
          )}
        </span>
      );
    }
    return stars;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <nav className="breadcrumb mb-8">
          <Link to="/" className="breadcrumb-item">Home</Link>
          <span className="breadcrumb-separator">/</span>
          <Link to="/products" className="breadcrumb-item">Products</Link>
          <span className="breadcrumb-separator">/</span>
          <span className="text-gray-500">{productData.name}</span>
        </nav>

        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="lg:grid lg:grid-cols-2 lg:gap-8">
            {/* Product Images */}
            <div className="p-6">
              <div className="aspect-w-1 aspect-h-1 mb-4">
                {productData.image_base64 ? (
                  <img
                    src={`data:image/jpeg;base64,${productData.image_base64}`}
                    alt={productData.name}
                    className="w-full h-96 object-cover rounded-lg"
                  />
                ) : (
                  <div className="w-full h-96 bg-gray-200 rounded-lg flex items-center justify-center">
                    <span className="text-gray-500 text-lg">No Image Available</span>
                  </div>
                )}
              </div>
            </div>

            {/* Product Info */}
            <div className="p-6">
              <div className="mb-4">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {productData.name}
                </h1>
                <div className="flex items-center space-x-2 mb-4">
                  <div className="flex items-center">
                    {renderStars(Math.floor(productData.average_rating || 0))}
                  </div>
                  <span className="text-sm text-gray-600">
                    ({productData.review_count || 0} reviews)
                  </span>
                </div>
                <p className="text-3xl font-bold text-primary-600 mb-4">
                  ${productData.price}
                </p>
              </div>

              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Description</h3>
                <p className="text-gray-600 leading-relaxed">
                  {productData.description}
                </p>
              </div>

              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-gray-600">
                    Category: <span className="font-medium">{productData.category}</span>
                  </span>
                  <span className="text-sm text-gray-600">
                    Stock: <span className="font-medium">{productData.stock} available</span>
                  </span>
                </div>

                {isAuthenticated && (
                  <div className="flex items-center space-x-4 mb-6">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium text-gray-700">
                        Quantity:
                      </label>
                      <select
                        value={quantity}
                        onChange={(e) => setQuantity(parseInt(e.target.value))}
                        className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        {[...Array(Math.min(10, productData.stock))].map((_, i) => (
                          <option key={i + 1} value={i + 1}>
                            {i + 1}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                <div className="flex space-x-4">
                  {isAuthenticated ? (
                    <button
                      onClick={handleAddToCart}
                      disabled={productData.stock === 0}
                      className="flex-1 btn-primary py-3 text-lg disabled:opacity-50"
                    >
                      {productData.stock === 0 ? 'Out of Stock' : 'Add to Cart'}
                    </button>
                  ) : (
                    <Link
                      to="/login"
                      className="flex-1 btn-primary py-3 text-lg text-center"
                    >
                      Login to Purchase
                    </Link>
                  )}
                  
                  <button className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50">
                    <HeartIcon className="h-6 w-6 text-gray-600" />
                  </button>
                  <button className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50">
                    <ShareIcon className="h-6 w-6 text-gray-600" />
                  </button>
                </div>
              </div>

              <div className="border-t pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Product Details
                </h3>
                <dl className="space-y-2">
                  <div className="flex justify-between">
                    <dt className="text-gray-600">SKU:</dt>
                    <dd className="text-gray-900">{productData._id}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Category:</dt>
                    <dd className="text-gray-900">{productData.category}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Availability:</dt>
                    <dd className={`${productData.stock > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {productData.stock > 0 ? 'In Stock' : 'Out of Stock'}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Related Products */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">Related Products</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* This would be populated with related products */}
            <div className="text-center text-gray-500 col-span-full">
              Related products will be shown here
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;