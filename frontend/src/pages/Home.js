import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import { productsAPI } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { 
  ShoppingBagIcon, 
  TruckIcon, 
  ShieldCheckIcon, 
  ArrowRightIcon 
} from '@heroicons/react/24/outline';

const Home = () => {
  const { data: productsData, isLoading } = useQuery(
    ['featured-products'],
    () => productsAPI.getProducts({ limit: 8, sort_by: 'created_at', order: 'desc' })
  );

  const features = [
    {
      name: 'Free Shipping',
      description: 'Free shipping on orders over $50',
      icon: TruckIcon,
    },
    {
      name: 'Secure Payment',
      description: 'Safe and secure payment processing',
      icon: ShieldCheckIcon,
    },
    {
      name: 'Quality Products',
      description: 'Carefully curated high-quality items',
      icon: ShoppingBagIcon,
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-primary-600 to-primary-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Welcome to <span className="text-secondary-400">TrendNest</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-primary-100">
              Discover the latest trends and shop with confidence
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/products"
                className="inline-flex items-center px-8 py-4 bg-white text-primary-600 font-semibold rounded-lg hover:bg-gray-100 transition-colors"
              >
                Shop Now
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Link>
              <Link
                to="/products"
                className="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-lg hover:bg-white hover:text-primary-600 transition-colors"
              >
                Browse Products
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Why Choose TrendNest?</h2>
            <p className="text-lg text-gray-600">We provide the best shopping experience with quality products and excellent service</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-4">
                  <feature.icon className="h-12 w-12 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.name}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Featured Products</h2>
            <p className="text-lg text-gray-600">Check out our latest and most popular items</p>
          </div>

          {isLoading ? (
            <LoadingSpinner size="lg" className="h-64" />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              {productsData?.data?.products?.slice(0, 8).map((product) => (
                <div key={product._id} className="product-card group">
                  <div className="aspect-w-1 aspect-h-1 w-full overflow-hidden rounded-t-xl">
                    {product.image_base64 ? (
                      <img
                        src={`data:image/jpeg;base64,${product.image_base64}`}
                        alt={product.name}
                        className="h-48 w-full object-cover group-hover:scale-105 transition-transform duration-200"
                      />
                    ) : (
                      <div className="h-48 w-full bg-gray-200 flex items-center justify-center">
                        <span className="text-gray-500">No Image</span>
                      </div>
                    )}
                  </div>
                  <div className="p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {product.name}
                    </h3>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      {product.description}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xl font-bold text-primary-600">
                        ${product.price}
                      </span>
                      <Link
                        to={`/products/${product._id}`}
                        className="btn-primary text-sm"
                      >
                        View Details
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="text-center mt-12">
            <Link
              to="/products"
              className="btn-primary px-8 py-3 text-lg"
            >
              View All Products
            </Link>
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="py-16 bg-primary-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Stay Updated</h2>
          <p className="text-xl mb-8 text-primary-100">
            Subscribe to our newsletter for the latest trends and exclusive offers
          </p>
          <form className="max-w-md mx-auto flex">
            <input
              type="email"
              placeholder="Enter your email"
              className="flex-1 px-4 py-3 rounded-l-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-300"
            />
            <button
              type="submit"
              className="px-6 py-3 bg-secondary-500 text-white rounded-r-lg hover:bg-secondary-600 transition-colors"
            >
              Subscribe
            </button>
          </form>
        </div>
      </section>
    </div>
  );
};

export default Home;