import React, { useState } from 'react';
import Header from './Header';
import Footer from './Footer';
import Sidebar from '.Sidebar';

const Layout = ({ children }) => {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const toggleSidebar = () => {
        setSidebarOpen(!sidebarOpen);
    };

    return (
        <div className='flex flex-col min-h-screen'>
            <Header toggleSidebar={toggleSidebar} />

            <div className="flex flex-1">
                <Sidebar isOpen={sidebarOpen} />

                <main className="flex-1 md:ml-64 p-6 bg-gray-50">
                    {/* Page Content */}
                    {children}
                </main>
            </div>

            <Footer />
        </div>
    );
};

export default Layout;