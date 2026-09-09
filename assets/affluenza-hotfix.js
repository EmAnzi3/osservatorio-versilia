(() => {
  'use strict';
  const nativeFetch = window.fetch.bind(window);
  const legacyArchive = 'data/affluenza/archive-00.b64';
  const chunks = ['archive-v2-00.b64', 'archive-v2-01.b64', 'archive-v2-02.b64', 'archive-v2-03.b64'];
  window.fetch = async (input, init) => {
    const url = typeof input === 'string' ? input : input?.url;
    if (!url || !url.includes(legacyArchive)) return nativeFetch(input, init);
    const responses = await Promise.all(chunks.map(name => nativeFetch(`../../../data/affluenza/${name}?v=20260909-hotfix1`, {cache: 'no-store'})));
    const failed = responses.find(response => !response.ok);
    if (failed) return failed;
    const encoded = (await Promise.all(responses.map(response => response.text()))).join('').replace(/\s+/g, '');
    return new Response(encoded, {status: 200, headers: {'Content-Type': 'text/plain; charset=utf-8'}});
  };
})();
