(() => {
  'use strict';

  const nativeFetch = window.fetch.bind(window);
  const compactPattern = /(?:^|\/)data\/compact-(\d{2})\.json(?:[?#].*)?$/;

  async function decodePart(index) {
    if (index >= 5) return [];
    if (typeof DecompressionStream !== 'function') {
      throw new Error('Browser non compatibile con il dataset compresso dei percorsi.');
    }
    const url = `data/routes-part-${String(index).padStart(2, '0')}.b64`;
    const response = await nativeFetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error(`Dataset percorsi non trovato: ${url}`);
    const b64 = (await response.text()).trim();
    const compressed = Uint8Array.from(atob(b64), char => char.charCodeAt(0));
    const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }

  window.fetch = async (input, init) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, document.baseURI);
    const match = compactPattern.exec(url.pathname);
    if (!match) return nativeFetch(input, init);

    const index = Number(match[1]);
    const data = await decodePart(index);
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json; charset=utf-8' }
    });
  };
})();
