export const colorPresets = [
  { name: 'Blue Night', colors: ['#1e293b', '#1e3a8a', '#312e81', '#1e293b'], primary: '#1e3a8a' },
  { name: 'Purple Dreams', colors: ['#1e1b4b', '#4c1d95', '#581c87', '#1e1b4b'], primary: '#4c1d95' },
  { name: 'Forest', colors: ['#14532d', '#065f46', '#064e3b', '#14532d'], primary: '#065f46' },
  { name: 'Sunset', colors: ['#7c2d12', '#9a3412', '#dc2626', '#7c2d12'], primary: '#dc2626' },
  { name: 'Ocean', colors: ['#0c4a6e', '#0369a1', '#0284c7', '#0c4a6e'], primary: '#0369a1' },
  { name: 'Midnight', colors: ['#000000', '#0a0a0a', '#050505', '#000000'], primary: '#4a5568' },
];

export const applyColorPreset = (presetIndex: number) => {
  const preset = colorPresets[presetIndex];
  if (!preset) return;

  // Use the dominant color (second color in the array) as solid background
  const backgroundColor = preset.colors[1];
  document.body.style.background = backgroundColor;
  document.body.style.backgroundSize = '';

  // Set CSS variables for the primary color and background
  const root = document.documentElement;
  root.style.setProperty('--primary', preset.primary);
  root.style.setProperty('--bg-color', backgroundColor);

  // Extract RGB values for the primary color
  const hex = preset.primary.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  root.style.setProperty('--primary-rgb', `${r}, ${g}, ${b}`);

  // Save to localStorage
  localStorage.setItem('colorPreset', presetIndex.toString());
};

export const loadSavedColorPreset = () => {
  const savedPreset = localStorage.getItem('colorPreset');
  if (savedPreset) {
    const presetIndex = parseInt(savedPreset, 10);
    if (!isNaN(presetIndex) && presetIndex < colorPresets.length) {
      applyColorPreset(presetIndex);
      return presetIndex;
    }
  }
  return 0; // Default to first preset
};
