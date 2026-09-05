// Stable entry point loaded by photo.html. Keep the proven v0.4 PDF generator
// active, then layer the terrain, topology, coverage and final contract audits.
import './brickhouse-survey-package-v04.js?v=pdf-handoff-0.4';
import './brickhouse-survey-package-v05.js?v=pdf-handoff-0.5-terrain-audit';
import './brickhouse-survey-package-v06.js?v=pdf-handoff-0.6-topology-audit';
import './brickhouse-survey-package-v07.js?v=pdf-handoff-0.7-coverage-audit';
import './brickhouse-survey-package-v08.js?v=pdf-handoff-0.8-final-contract-audit';
import './brickhouse-survey-package-v09.js?v=pdf-handoff-0.9-measurement-provenance';
// Reject any AI-claimed user measurement that is not exactly authorized by the
// current capture inputs before Survey validation or Scene handoff can run.
import './survey-measurement-provenance-gate.js?v=measurement-provenance-gate-0.1';
// Also lock Survey → Scene prompt fetches to the currently validated Survey so
// stale browser state or a model's remembered IDs cannot silently replace it.
import './scene-handoff-source-lock.js?v=scene-handoff-source-lock-0.1';
// Render the images actually selected in every capture slot, including files
// inserted programmatically by the benchmark preloader.
import './photo-slot-previews.js?v=photo-slot-previews-0.1';
// Load the restored phone-first cockpit with a fresh cache key.
import './photo-shell-loader.js?v=single-screen-1.1';
// Dedicated opt-in benchmark preload. Normal photo.html visits remain untouched;
// only ?benchmark=real-house-5 loads the five versioned reference photos.
import './real-house-benchmark-loader.js?v=real-house-5-preload-0.1';
