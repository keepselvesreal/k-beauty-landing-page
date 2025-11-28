import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

// Using a reindeer SVG icon directly for "Santa Here" vibe
const ReindeerIcon = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M5 12c-1.1 0-2 .9-2 2v2a4 4 0 0 0 4 4h10a4 4 0 0 0 4-4v-2c0-1.1-.9-2-2-2" />
    <path d="M12 4v8" />
    <path d="M12 12c0-3 2.5-3 3.5-5 .6-1.3 1.5-2 2.5-2" />
    <path d="M12 12c0-3-2.5-3-3.5-5-.6-1.3-1.5-2-2.5-2" />
    <circle cx="12" cy="14" r="2" fill="currentColor" className="text-[#8B5E5E]" />
  </svg>
);

const Header: React.FC = () => {
  const [language, setLanguage] = useState<'Tagalog' | 'English'>('Tagalog');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const selectLanguage = (selectedLang: 'Tagalog' | 'English') => {
    setLanguage(selectedLang);
    setIsDropdownOpen(false);
  };

  const otherLanguage = language === 'Tagalog' ? 'English' : 'Tagalog';

  return (
    <header className="w-full py-6 px-4 md:px-12 border-b border-gray-100 bg-white sticky top-0 z-50 flex items-center justify-between relative">
      {/* Spacer for left side to maintain visual balance if needed */}
      <div className="hidden md:block w-32"></div>

      {/* Centered Brand - Absolute positioning ensures it is perfectly centered relative to the container */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-0">
        <div className="flex items-center cursor-pointer whitespace-nowrap">
          <ReindeerIcon className="w-12 h-12 text-[#C49A9A] mr-3" />
          <span className="text-4xl font-bold tracking-tight text-gray-900">Santa Here</span>
        </div>
      </div>

      {/* Right Side: Language Toggle */}
      <div className="relative z-10 ml-auto md:ml-0">
        <button
          onClick={toggleDropdown}
          className="flex items-center justify-between space-x-2 bg-[#C49A9A] text-white px-4 py-2 rounded-full hover:bg-[#b08585] transition-colors text-sm font-medium w-32 shadow-sm"
        >
          <span className="flex-1 text-center">{language}</span>
          <ChevronDown
            className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`}
          />
        </button>

        {/* Language Dropdown */}
        {isDropdownOpen && (
          <div className="absolute top-full right-0 mt-2 w-32 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden py-1 animate-in fade-in slide-in-from-top-1 duration-200">
            <button
              onClick={() => selectLanguage(otherLanguage)}
              className="w-full px-4 py-2.5 text-sm text-gray-700 hover:bg-[#F9F5F2] hover:text-[#C49A9A] transition-colors text-center font-medium"
            >
              {otherLanguage}
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
