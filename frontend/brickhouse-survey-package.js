// Stable entry point loaded by photo.html. Register the hybrid PDF generator
// first so its capture listener owns the download while the proven v0.4
// implementation remains available as historical fallback code.
import './brickhouse-survey-hybrid-pdf.js?v=pdf-handoff-0.10-hybrid-text';
import './brickhouse-survey-package-v04.js?v=pdf-handoff-0.4';
import './brickhouse-survey-package-v05.js?v=pdf-handoff-0.5-terrain-audit';
import './brickhouse-survey-package-v06.js?v=pdf-handoff-0.6-topology-audit';
import './brickhouse-survey-package-v07.js?v=pdf-handoff-0.7-coverage-audit';
import './brickhouse-survey-package-v08.js?v=pdf-handoff-0.8-final-contract-audit';
import './brickhouse-survey-package-v09.js?v=pdf-handoff-0.9-measurement-provenance';
import './brickhouse-survey-package-v11.js?v=pdf-handoff-0.11-orientation-provenance';
// Reject any AI-claimed user measurement that is not exactly authorized by the
// current capture inputs before Survey validation or Scene handoff can run.
import './survey-measurement-provenance-gate.js?v=measurement-provenance-gate-0.1';
// Preserve photo capture-slot identity as provenance and reject silent facade
// permutations before Survey validation or Scene handoff can run.
import './survey-photo-orientation-provenance-gate.js?v=orientation-provenance-gate-0.1';
// Also lock Survey → Scene prompt fetches to the currently validated Survey so
// stale browser state or a model's remembered IDs cannot silently replace it.
import './scene-handoff-source-lock.js?v=scene-handoff-source-lock-0.1';
// Append the strict v4.4 serialization/contact audit to every active
// Survey → Scene prompt fetch before the handoff generator requests it.
import './scene-handoff-contract-audit-v44.js?v=scene-handoff-contract-audit-4.4';
// Make the Scene stage output-exclusive after all prior reasoning/audit layers:
// the accepted Survey is immutable input and only ArchitecturalScene may leave.
import './scene-handoff-stage-lock-v45.js?v=scene-handoff-stage-lock-4.5';
// Render the images actually selected in every capture slot, including files
// inserted programmatically by the benchmark preloader.
import './photo-slot-previews.js?v=photo-slot-previews-0.1';
// Load the restored phone-first cockpit with a fresh cache key.
import './photo-shell-loader.js?v=single-screen-1.1';
// Dedicated opt-in benchmark preload. Normal photo.html visits remain untouched;
// ?benchmark=real-house-5 loads the five versioned photos, while &stage=scene
// additionally reuses the accepted Survey through the normal validation path.
import './real-house-benchmark-loader.js?v=real-house-5-preload-0.2-scene-checkpoint';
