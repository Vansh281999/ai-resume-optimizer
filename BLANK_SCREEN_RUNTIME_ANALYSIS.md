# Blank Screen Runtime Analysis

## Root Cause

The React application was **not mounting properly** due to multiple issues:

### 1. Missing `basename` on BrowserRouter (FIXED)

**File:** `src/main.tsx` - Line 53
```tsx
<BrowserRouter basename="/ai-resume-optimizer">
```

When `base: '/ai-resume-optimizer/'` is set in vite.config.ts, the BrowserRouter needs the matching `basename` prop to handle client-side routing correctly. Without it, React Router cannot match routes and renders nothing.

### 2. Unsafe `window.matchMedia` call (FIXED)

**File:** `src/contexts/ThemeContext.tsx` - Line 19
```tsx
if (typeof window !== 'undefined' && window.matchMedia) {
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}
```

### 3. Missing useEffect in Analytics (FIXED)

**File:** `src/pages/Analytics.tsx` - Added missing `useEffect` hooks:
```tsx
useEffect(() => {
  trendsQuery.refetch();
}, []);

useEffect(() => {
  if (trendsQuery.error) {
    addToast(trendsQuery.error, 'info');
  }
}, [trendsQuery.error, addToast]);
```

### 4. Added global error handling (FIXED)

**File:** `src/main.tsx` - Wrapped render in try-catch to catch mount errors

## Verification

1. Hard refresh at `http://localhost:5173/ai-resume-optimizer/`
2. Check browser console for "main loaded", "creating root", "App rendering" logs
3. If there's still a blank page, check for "Mount Error" displayed in the DOM