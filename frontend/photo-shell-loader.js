const shellStylesheetId = 'boldungo-photo-shell-styles';

if (!document.getElementById(shellStylesheetId)) {
  const link = document.createElement('link');
  link.id = shellStylesheetId;
  link.rel = 'stylesheet';
  link.href = new URL('./photo-shell.css?v=single-screen-0.6', import.meta.url).href;
  document.head.appendChild(link);
}

import('./photo-shell.js?v=single-screen-0.7');
import('./survey-import-feedback-guard.js?v=survey-feedback-0.8');
import('./copy-feedback.js?v=feedback-copy-0.1');
