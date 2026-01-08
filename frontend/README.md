# Minecraft Server Manager - Frontend

Frontend application for the Minecraft Server Management Platform built with React 18, TypeScript, Vite, and Glassmorphism 2.0 UI.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3 with Glassmorphism 2.0
- **Routing**: React Router v6
- **State Management**: Zustand
- **Server State**: TanStack Query (React Query v5)
- **API Client**: Axios with JWT interceptors
- **Animations**: Framer Motion
- **Forms**: React Hook Form + Zod validation
- **Icons**: Lucide React
- **Charts**: Recharts

## Project Structure

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios instance with interceptors
│   │   ├── auth.ts            # Auth API methods
│   │   └── servers.ts         # Server API methods
│   ├── components/
│   │   ├── common/
│   │   │   ├── GlassCard.tsx
│   │   │   ├── GlassButton.tsx
│   │   │   └── GlassInput.tsx
│   │   ├── layout/
│   │   ├── server/
│   │   ├── mods/
│   │   ├── backups/
│   │   └── charts/
│   ├── pages/
│   ├── hooks/
│   ├── store/
│   │   ├── authStore.ts       # Authentication state
│   │   └── uiStore.ts         # UI state
│   ├── lib/
│   │   └── queryClient.ts     # TanStack Query config
│   ├── utils/
│   │   ├── cn.ts              # Class name utility
│   │   ├── formatters.ts      # Data formatters
│   │   └── constants.ts       # App constants
│   ├── types/
│   │   ├── server.ts
│   │   ├── user.ts
│   │   └── api.ts
│   ├── styles/
│   │   ├── globals.css
│   │   └── glassmorphism.css
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── .eslintrc.cjs
```

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

The dev server runs on `http://localhost:5173` with the following features:

- Hot Module Replacement (HMR)
- API proxy to backend (`/api` → `http://localhost:5000`)
- WebSocket proxy for Socket.io (`/socket.io` → `http://localhost:5000`)
- TypeScript type checking
- ESLint for code quality

## API Integration

The frontend uses Axios for API communication with:

- JWT bearer token authentication
- Automatic token refresh on 401 errors
- Request/response interceptors
- 30-second timeout
- TypeScript types for all endpoints

## State Management

### Auth Store (Zustand)
- User authentication state
- Token management
- Persistent storage

### UI Store (Zustand)
- Sidebar state
- Theme preferences
- UI controls

### Server State (TanStack Query)
- Server data fetching
- Automatic refetching
- Caching & invalidation
- Optimistic updates

## Glassmorphism 2.0 Components

All UI components use the glassmorphism design system:

- **GlassCard**: Container with backdrop blur and transparency
- **GlassButton**: Interactive buttons with hover animations
- **GlassInput**: Form inputs with focus states
- Consistent color scheme with blue/purple gradients
- Status indicators for servers (running, stopped, error, etc.)

## Environment Variables

Create a `.env` file if needed for custom configuration:

```env
VITE_API_URL=http://localhost:5000
```

## Features Ready

- ✅ Vite dev server with HMR
- ✅ Tailwind CSS configured
- ✅ Glassmorphism UI components
- ✅ API client with JWT auth
- ✅ Zustand stores
- ✅ TanStack Query setup
- ✅ TypeScript types
- ✅ Utility functions
- ✅ Proxy to backend

## Next Steps

This frontend core is ready for Track 4: Features & Integration

- Build authentication pages (Login, Register)
- Create server management dashboard
- Implement real-time metrics
- Add mod & backup management
- Connect to backend APIs
- Add Socket.io for live updates
