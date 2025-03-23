import React from 'react';
import { Github, Mail } from 'lucide-react';

const Footer = () => {
    return (
        <footer className="bg-gray-800 text-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* About section */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">About</h3>
                        <p className="text-gray-300 text-sm">
                            LSTM Stock Predictor uses advanced machine learning to help you make informed decisions.
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
                        <ul className="space-y-2 text-gray-300 text-sm">
                            <li><a href="/about" className="hover:text-white">About</a></li>
                            <li><a href="/documentation" className="hover:text-white">Documentation</a></li>
                            <li><a href="/privacy" className="hover:text-white">Privacy Policy</a></li>
                            <li><a href="/terms" className="hover:text-white">Terms of Service</a></li>
                        </ul>
                    </div>

                    {/* Contact section */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Contact</h3>
                        <div className="space-y-4">
                            <a href="mailto:ajm2327@nau.edu" className="flex items-center text-gray-300 hover:text-white text-sm">
                                <Mail className="h-5 w-5 mr-2" />
                                ajm2327@nau.edu
                            </a>
                            <a href="https://github.com/ajm2327/LSTM_webApp" className="flex items-center text-gray-300 hover:text-white text-sm">
                                <Github className="h-5 w-5 mr-2" />
                                Github Repository
                            </a>
                        </div>
                    </div>
                </div>

                <div className="mt-8 pt-8 border-t border-gray-700 text-center text-gray-300 text-sm">
                    <p>&copy; {new Date().getFullYear()} LSTM Stock Predictor. All rights reserved</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;