import { useState, useEffect } from 'react';

export type SkinMode = 'dark' | 'light';

const STORAGE_KEY = 'dalisports_skin';

export const useSkin = () => {
  const [skin, setSkinState] = useState<SkinMode>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as SkinMode | null;
      if (saved === 'light' || saved === 'dark') {
        return saved;
      }
    } catch (e) {
      console.warn('Could not read skin from localStorage:', e);
    }
    return 'dark';
  });

  const applySkinToDom = (newSkin: SkinMode) => {
    try {
      document.documentElement.setAttribute('data-skin', newSkin);
      document.body.setAttribute('data-skin', newSkin);

      if (newSkin === 'light') {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
      } else {
        document.documentElement.classList.remove('light');
        document.documentElement.classList.add('dark');
      }
    } catch (e) {
      console.warn('Error applying skin to DOM:', e);
    }
  };

  const setSkin = (newSkin: SkinMode) => {
    setSkinState(newSkin);
    try {
      localStorage.setItem(STORAGE_KEY, newSkin);
    } catch (e) {
      console.warn('Could not save skin to localStorage:', e);
    }
    applySkinToDom(newSkin);
  };

  const toggleSkin = () => {
    setSkin(skin === 'dark' ? 'light' : 'dark');
  };

  useEffect(() => {
    applySkinToDom(skin);
  }, [skin]);

  return { skin, setSkin, toggleSkin };
};
