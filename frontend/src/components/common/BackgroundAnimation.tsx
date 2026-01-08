import React from 'react';

export const BackgroundAnimation: React.FC = () => {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Floating Geometric Shapes */}

      {/* Large Circle - top right */}
      <div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-float-slow" />

      {/* Medium Circle - bottom left */}
      <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-purple-500/10 rounded-full blur-2xl animate-float-medium" />

      {/* Square - top left */}
      <div className="absolute top-20 left-20 w-32 h-32 bg-cyan-500/5 rotate-45 blur-xl animate-float-fast" />

      {/* Triangle - middle right */}
      <div className="absolute top-1/3 right-20">
        <div className="w-0 h-0 border-l-[80px] border-l-transparent border-r-[80px] border-r-transparent border-b-[140px] border-b-indigo-500/10 blur-xl animate-float-slow" />
      </div>

      {/* Hexagon - bottom center */}
      <div className="absolute bottom-32 left-1/2 -translate-x-1/2">
        <svg width="120" height="120" viewBox="0 0 120 120" className="opacity-10 blur-md animate-rotate-slow">
          <polygon
            points="60,10 100,35 100,85 60,110 20,85 20,35"
            fill="currentColor"
            className="text-pink-500"
          />
        </svg>
      </div>

      {/* Diamond - top center */}
      <div className="absolute top-40 left-1/3 w-24 h-24 bg-violet-500/8 rotate-45 blur-lg animate-float-medium" />

      {/* Small Circle - middle */}
      <div className="absolute top-1/2 left-1/4 w-40 h-40 bg-emerald-500/10 rounded-full blur-2xl animate-float-fast" />

      {/* Pentagon - bottom right */}
      <div className="absolute bottom-40 right-1/4">
        <svg width="100" height="100" viewBox="0 0 100 100" className="opacity-10 blur-md animate-float-slow">
          <polygon
            points="50,10 90,40 75,85 25,85 10,40"
            fill="currentColor"
            className="text-amber-500"
          />
        </svg>
      </div>

      {/* Octagon - left center */}
      <div className="absolute top-2/3 left-16">
        <svg width="80" height="80" viewBox="0 0 80 80" className="opacity-10 blur-lg animate-rotate-slow-reverse">
          <polygon
            points="30,10 50,10 70,30 70,50 50,70 30,70 10,50 10,30"
            fill="currentColor"
            className="text-rose-500"
          />
        </svg>
      </div>

      {/* Star - top middle */}
      <div className="absolute top-1/4 right-1/3">
        <svg width="90" height="90" viewBox="0 0 90 90" className="opacity-10 blur-md animate-pulse-slow">
          <polygon
            points="45,10 55,35 82,35 60,52 70,77 45,60 20,77 30,52 8,35 35,35"
            fill="currentColor"
            className="text-sky-500"
          />
        </svg>
      </div>

      {/* Rectangle - right side */}
      <div className="absolute top-1/4 right-32 w-40 h-24 bg-fuchsia-500/8 rotate-12 blur-xl animate-float-medium" />

      {/* Small decorative dots */}
      <div className="absolute top-1/2 right-1/2 w-3 h-3 bg-blue-400/20 rounded-full animate-ping-slow" />
      <div className="absolute top-1/3 left-2/3 w-2 h-2 bg-purple-400/20 rounded-full animate-ping-slow delay-1000" />
      <div className="absolute bottom-1/3 left-1/3 w-4 h-4 bg-cyan-400/20 rounded-full animate-ping-slow delay-2000" />
    </div>
  );
};
