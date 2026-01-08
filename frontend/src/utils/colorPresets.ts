export const colorPresets = [
  { name: 'Blue Night', colors: ['#1e293b', '#1e3a8a', '#312e81', '#1e293b'] },
  { name: 'Purple Dreams', colors: ['#1e1b4b', '#4c1d95', '#581c87', '#1e1b4b'] },
  { name: 'Forest', colors: ['#14532d', '#065f46', '#064e3b', '#14532d'] },
  { name: 'Sunset', colors: ['#7c2d12', '#9a3412', '#dc2626', '#7c2d12'] },
  { name: 'Ocean', colors: ['#0c4a6e', '#0369a1', '#0284c7', '#0c4a6e'] },
  { name: 'Midnight', colors: ['#0f172a', '#1e1b4b', '#18181b', '#0f172a'] },
];

export const applyColorPreset = (presetIndex: number) => {
  const preset = colorPresets[presetIndex];
  if (!preset) return;

  // Apply the gradient to the body
  const gradientString = `linear-gradient(-45deg, ${preset.colors.join(', ')})`;
  document.body.style.background = gradientString;
  document.body.style.backgroundSize = '400% 400%';

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
