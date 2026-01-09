import React from 'react';

export const BackgroundAnimation: React.FC = () => {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Circle 1 */}
      <div className="absolute w-24 h-24 opacity-5 animate-bubble-1">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-1">
          <circle cx="50" cy="50" r="45" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* Plus 1 */}
      <div className="absolute w-16 h-16 opacity-5 animate-bubble-2">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-2">
          <rect x="40" y="10" width="20" height="80" fill="currentColor" className="text-white" />
          <rect x="10" y="40" width="80" height="20" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* X 1 */}
      <div className="absolute w-20 h-20 opacity-5 animate-bubble-3">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-3">
          <rect x="40" y="10" width="20" height="80" fill="currentColor" className="text-white" transform="rotate(45 50 50)" />
          <rect x="40" y="10" width="20" height="80" fill="currentColor" className="text-white" transform="rotate(-45 50 50)" />
        </svg>
      </div>

      {/* Triangle 1 */}
      <div className="absolute w-28 h-28 opacity-5 animate-bubble-4">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-4">
          <polygon points="50,10 90,85 10,85" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* Square 1 */}
      <div className="absolute w-20 h-20 opacity-5 animate-bubble-5">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-5">
          <rect x="10" y="10" width="80" height="80" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* Play button */}
      <div className="absolute w-24 h-24 opacity-5 animate-bubble-6">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-6">
          <polygon points="30,20 30,80 75,50" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* Circle 2 */}
      <div className="absolute w-16 h-16 opacity-5 animate-bubble-7">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-7">
          <circle cx="50" cy="50" r="45" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* Plus 2 */}
      <div className="absolute w-14 h-14 opacity-5 animate-bubble-8">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-8">
          <rect x="40" y="10" width="20" height="80" fill="currentColor" className="text-white" />
          <rect x="10" y="40" width="80" height="20" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* X 2 */}
      <div className="absolute w-18 h-18 opacity-5 animate-bubble-9">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-9">
          <rect x="40" y="10" width="20" height="80" fill="currentColor" className="text-white" transform="rotate(45 50 50)" />
          <rect x="40" y="10" width="20" height="80" fill="currentColor" className="text-white" transform="rotate(-45 50 50)" />
        </svg>
      </div>

      {/* Square 2 */}
      <div className="absolute w-16 h-16 opacity-5 animate-bubble-10">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-10">
          <rect x="10" y="10" width="80" height="80" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* Triangle 2 */}
      <div className="absolute w-22 h-22 opacity-5 animate-bubble-11">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-1">
          <polygon points="50,10 90,85 10,85" fill="currentColor" className="text-white" />
        </svg>
      </div>

      {/* Circle 3 */}
      <div className="absolute w-20 h-20 opacity-5 animate-bubble-12">
        <svg viewBox="0 0 100 100" className="w-full h-full animate-size-slow-3">
          <circle cx="50" cy="50" r="45" fill="currentColor" className="text-white" />
        </svg>
      </div>
    </div>
  );
};
