// The current Boldungo mobile shell is owned by photo.html + mobile-shell.css
// + mobile-shell-state.js. Keep this stable loader only for import feedback guards.
// Do not load the legacy photo-shell.js/photo-shell.css cockpit: it rewrites the
// page DOM, locks body scrolling, and can make the live workflow appear truncated.
import('./survey-import-feedback-guard.js?v=survey-feedback-0.8');
