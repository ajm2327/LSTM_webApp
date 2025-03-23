import React from 'react';
import { Menu, Search } from 'lucide-react';

const Header = ({ toggleSidebar }) => {
    return (
        <header className="bg-white shadow-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    {/* Left section w logo/brand */}
                    <div className="flex items-center">
                        <button
                            onClick={toggleSidebar}
                            className="p-2 rounded-md text-gray-600 hover:text-gray-900 focus:outline-none md:hidden"
                        >
                            <Menu className="h-6 w-6" />
                        </button>
                        <div className="ml-4 font-bold text-xl text-gray-900">LSTM STOCK PREDICTOR</div>
                    </div>

                    {/* Center section with Search */}
                    <div className="flex-1 max-w-lg mx-4">
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Search className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                type="text"
                                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                placeholder="Search stocks..."
                            />
                        </div>
                    </div>

                    {/* Right section with nav items */}
                    <div className="flex items-center space-x-4">
                        <nav classname="hidden md:flex space-x-4">
                            <a href="/dashboard" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                                Dashboard
                            </a>
                            <a href="/predictions" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                                Predictions
                            </a>
                            <a href="/settings" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                                Settings
                            </a>
                        </nav>
                        <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                            Login
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;