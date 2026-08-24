const BENCHMARK_ROOT = './benchmarks';

async function fetchJson(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

export async function loadBundledBenchmark(id) {
  if (!/^[a-z0-9-]+$/.test(id)) throw new Error('Invalid benchmark id');
  const root = `${BENCHMARK_ROOT}/${id}`;
  const manifest = await fetchJson(`${root}/manifest.json`);
  if (manifest.id !== id) throw new Error(`Benchmark manifest id mismatch: ${manifest.id}`);
  if (!Array.isArray(manifest.photos) || manifest.photos.length === 0) {
    throw new Error(`Benchmark ${id} has no photos`);
  }

  const photos = [];
  for (const entry of manifest.photos) {
    if (typeof entry.path !== 'string' || entry.path.includes('..') || entry.path.startsWith('/')) {
      throw new Error(`Unsafe benchmark photo path for index ${entry.photo_index}`);
    }
    const response = await fetch(`${root}/${entry.path}`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`${entry.path}: HTTP ${response.status}`);
    const blob = await response.blob();
    const type = blob.type || 'image/jpeg';
    photos.push({
      ...entry,
      file: new File([blob], entry.path.split('/').pop(), { type }),
    });
  }
  return { manifest, photos };
}
