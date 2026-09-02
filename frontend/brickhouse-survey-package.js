// Stable entry point loaded by photo.html. Keep the proven v0.4 PDF generator
// active, then layer the terrain, topology, coverage and final contract audits.
import './brickhouse-survey-package-v04.js?v=pdf-handoff-0.4';
import './brickhouse-survey-package-v05.js?v=pdf-handoff-0.5-terrain-audit';
import './brickhouse-survey-package-v06.js?v=pdf-handoff-0.6-topology-audit';
import './brickhouse-survey-package-v07.js?v=pdf-handoff-0.7-coverage-audit';
import './brickhouse-survey-package-v08.js?v=pdf-handoff-0.8-final-contract-audit';
// Also lock Survey → Scene prompt fetches to the currently validated Survey so
// stale browser state or a model's remembered IDs cannot silently replace it.
import './scene-handoff-source-lock.js?v=scene-handoff-source-lock-0.1';
// Keep the shell loader cache key in sync with the deployed HUD revision.
import './photo-shell-loader.js?v=single-screen-0.9';
