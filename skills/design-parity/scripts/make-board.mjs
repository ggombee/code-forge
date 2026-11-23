import { readFile, writeFile } from 'node:fs/promises';
import { basename, resolve } from 'node:path';

const usage = 'Usage: node make-board.mjs <reference.png|jpg|webp> <actual.png|jpg|webp> <new-output.html>';
const args = process.argv.slice(2);

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}

async function image(path) {
  const data = await readFile(path);
  let mime;
  if (data.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    mime = 'image/png';
  } else if (data[0] === 0xff && data[1] === 0xd8 && data[2] === 0xff) {
    mime = 'image/jpeg';
  } else if (data.toString('ascii', 0, 4) === 'RIFF' && data.toString('ascii', 8, 12) === 'WEBP') {
    mime = 'image/webp';
  } else {
    throw new Error(`Unsupported image format: ${path} (PNG, JPEG or WebP required)`);
  }
  return { name: escapeHtml(basename(path)), url: `data:${mime};base64,${data.toString('base64')}` };
}

async function main() {
  if (args.length === 1 && args[0] === '--help') {
    console.log(usage);
    return;
  }
  if (args.length !== 3) throw new Error(usage);
  const [reference, actual] = await Promise.all(args.slice(0, 2).map(image));
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<title>Design parity comparison</title>
<style>
:root { color-scheme: light dark; font: 16px system-ui, sans-serif; }
body { margin: 24px; }
header { max-width: 70ch; }
.controls { display: flex; flex-wrap: wrap; gap: 16px; margin: 20px 0; }
.frames { display: flex; gap: 24px; overflow: auto; }
figure { margin: 0; min-width: 0; flex: 1; }
figcaption { margin-bottom: 8px; overflow-wrap: anywhere; }
.viewport { overflow: auto; border: 1px solid GrayText; }
img { display: block; max-width: none; }
#overlay { overflow: auto; }
.stack { position: relative; width: max-content; }
#overlay-actual { position: absolute; inset: 0; opacity: .5; }
[hidden] { display: none !important; }
</style>
</head>
<body>
<header>
<h1>Design parity comparison</h1>
<p>Local visual aid, not a pass/fail score. Images stay at their natural pixel size; scroll to inspect. Confirm matching viewport, DPR, theme, data and UI state separately.</p>
<p id="status" role="status">Loading images…</p>
</header>
<div class="controls">
<label>View <select id="mode"><option value="side">Side by side</option><option id="overlay-option" value="overlay" disabled>Overlay</option></select></label>
<label>Implementation opacity <input id="opacity" type="range" min="0" max="100" value="50" disabled></label>
</div>
<div id="side" class="frames">
<figure><figcaption>Reference: ${reference.name}</figcaption><div class="viewport"><img id="reference" src="${reference.url}" alt="Reference screenshot"></div></figure>
<figure><figcaption>Implementation: ${actual.name}</figcaption><div class="viewport"><img id="actual" src="${actual.url}" alt="Implementation screenshot"></div></figure>
</div>
<div id="overlay" hidden><div class="stack"><img src="${reference.url}" alt="Reference screenshot"><img id="overlay-actual" src="${actual.url}" alt="Implementation overlay"></div></div>
<script>
const reference = document.getElementById('reference');
const actual = document.getElementById('actual');
const status = document.getElementById('status');
const mode = document.getElementById('mode');
const opacity = document.getElementById('opacity');
Promise.all([reference.decode(), actual.decode()]).then(() => {
  const same = reference.naturalWidth === actual.naturalWidth && reference.naturalHeight === actual.naturalHeight;
  status.textContent = 'Reference ' + reference.naturalWidth + '×' + reference.naturalHeight + '; implementation ' + actual.naturalWidth + '×' + actual.naturalHeight + '. ' + (same ? 'Dimensions match; visual review still required.' : 'Dimensions differ. Overlay disabled; recapture with matching conditions.');
  document.getElementById('overlay-option').disabled = !same;
}).catch(() => {
  status.textContent = 'Image decoding failed. Replace the invalid capture before comparing.';
});
mode.addEventListener('change', () => {
  const overlay = mode.value === 'overlay';
  document.getElementById('side').hidden = overlay;
  document.getElementById('overlay').hidden = !overlay;
  opacity.disabled = !overlay;
});
opacity.addEventListener('input', () => {
  document.getElementById('overlay-actual').style.opacity = opacity.value / 100;
});
</script>
</body>
</html>
`;
  await writeFile(args[2], html, { flag: 'wx' });
  console.log(`Created ${resolve(args[2])}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
