import React from 'react';
import {
    LayoutDashboard,
    LineChart,
    Settings,
    History,
    Star,
    BookOpen
} from 'lucide-react';

const Sidebar = ({ isOpen }) => {
    const menuItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
        { icon: LineChart, label: 'Predictions', path: '/predictions' },
        { icon: History, label: 'History', path: '/history' },
        { icon: Star, label: 'Favorites', path: '/favorites' },
        { icon: BookOpen, label: 'Documentation', path: '/docs' },
        { icon: Settings, label: 'Settings', path: '/settings' }
    ];

    return (
        <aside className={`
            bg-gray-800 text-white w-64 min-h-screen
            fixed left-0 top-0 transform transition-transform duration-200 ease-in-out
            ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0
            `}>
            <div className="p-4">
                <div className="text-xl font-bold mb-8 text-center">LSTM Tool</div>

                <nav className="space-y-2">
                    {menuItems.map((item, index) => {
                        const Icon = item.icon;
                        return (
                            <a
                                key={index}
                                href={item.path}
                                className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-700 transition-colors"
                            >
                                <Icon className="h-5 w-5" />
                                <space>{item.label}</space>
                            </a>
                        );
                    })};
                </nav>
            </div>

            {/* User section at bottom */}
            <div className="absolute bottom-0 left-0 right-0 p-4">
                <div className="border-t border-gray-700 pt-4">
                    <div className="flex items-center space-x-3 px-4">
                        <div className="w-8 h-8 rounded-full bg-gray-600" />
                        <div>
                            <div className="text-sm font-medium">User Name</div>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;