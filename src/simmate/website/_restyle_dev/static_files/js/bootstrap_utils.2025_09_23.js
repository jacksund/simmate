/*!
 * modified from: https://getbootstrap.com/docs/5.3/customize/color-modes/#javascript
 * 
 * Example of access the current theme elsewhere...
 *  From localStorage (the saved preference)
 *    const themeStored = localStorage.getItem('theme'); // 'light', 'dark', or 'auto'
 *  From the current document theme
 *    const themeActive = document.documentElement.getAttribute('data-bs-theme'); // 'light' or 'dark'
 */

// Allows the user preference to be stored and carry through page reload
(() => {
  const setTheme = theme => {
    document.documentElement.setAttribute('data-bs-theme', theme);
  };

  const applyTheme = theme => {
    localStorage.setItem('theme', theme);
    setTheme(theme);
  };

  document.addEventListener('DOMContentLoaded', () => {
    // default to dark
    const stored = localStorage.getItem('theme');
    const theme = stored || 'dark';
    applyTheme(theme);

    // handle dropdown clicks
    document.querySelectorAll('[data-bs-theme-value]').forEach(btn => {
      btn.addEventListener('click', () => applyTheme(btn.dataset.bsThemeValue));
    });
  });
})();
