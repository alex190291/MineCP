# Quick Start Guide

## Installation

```bash
cd /data/minecraft/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Access

Open your browser to: **http://localhost:5173**

## What You'll See

The showcase page demonstrates:
- Glassmorphism card components
- Interactive hover effects
- Button variants (primary, secondary, danger, ghost)
- Form inputs with labels and error states
- Status indicators (running, stopped, starting, error)
- Gradient text effects
- Backdrop blur and transparency

## Testing the Proxy

With the backend running on port 5000, the Vite dev server will proxy:
- `/api/*` → `http://localhost:5000/api/*`
- `/socket.io/*` → `http://localhost:5000/socket.io/*` (WebSocket)

## Available Scripts

```bash
npm run dev      # Start dev server (port 5173)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

## File Structure

```
frontend/
├── src/
│   ├── api/              # API client & services
│   ├── components/       # UI components
│   │   └── common/       # GlassCard, GlassButton, GlassInput
│   ├── store/            # Zustand stores
│   ├── utils/            # Utilities & formatters
│   ├── types/            # TypeScript types
│   └── styles/           # CSS files
├── public/               # Static assets
└── [config files]        # Vite, TS, Tailwind, etc.
```

## Key Components

### GlassCard
```tsx
import { GlassCard } from '@/components/common/GlassCard';

<GlassCard hover onClick={() => console.log('clicked')}>
  Content here
</GlassCard>
```

### GlassButton
```tsx
import { GlassButton } from '@/components/common/GlassButton';

<GlassButton variant="primary" size="md" loading={false}>
  Click Me
</GlassButton>
```

### GlassInput
```tsx
import { GlassInput } from '@/components/common/GlassInput';

<GlassInput
  label="Server Name"
  placeholder="Enter name..."
  error="Optional error message"
/>
```

## Using the API Client

```tsx
import { serversAPI } from '@/api/servers';
import { useQuery } from '@tanstack/react-query';

// In a component
const { data: servers } = useQuery({
  queryKey: ['servers'],
  queryFn: serversAPI.getAll,
});
```

## Using Zustand Stores

```tsx
import { useAuthStore } from '@/store/authStore';

// In a component
const { user, isAuthenticated, setAuth, clearAuth } = useAuthStore();

// Login
setAuth(userData, accessToken, refreshToken);

// Logout
clearAuth();
```

## Troubleshooting

### Port already in use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 3000
```

### Dependency issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript errors
```bash
# Check TypeScript compilation
npx tsc --noEmit
```

## Next Steps

After verifying the frontend core:
1. Implement authentication pages
2. Build server dashboard
3. Add real-time metrics
4. Connect to backend APIs
5. Implement mod & backup management

**Ready for Track 4: Features & Integration**
