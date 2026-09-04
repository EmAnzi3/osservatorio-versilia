(() => {
  'use strict';
  if (globalThis.__OV_AGRI2_DRAFT_INSTALLED__) return;
  globalThis.__OV_AGRI2_DRAFT_INSTALLED__ = true;

  const scriptUrl = globalThis.__OV_SCRIPT_URL__ || document.currentScript?.src || location.href;
  const overlayUrl = new URL('../data/agricoltura-ii-draft.json', scriptUrl).href;
  const nativeFetch = globalThis.fetch.bind(globalThis);

  function isSiteDataRequest(input) {
    try {
      const raw = input instanceof Request ? input.url : String(input);
      return new URL(raw, location.href).pathname.endsWith('/data/site-data.json');
    } catch (_) {
      return false;
    }
  }

  function mergeDraft(data, overlay) {
    if (!data?.metrics || !data?.themes?.[overlay.theme]) return data;
    Object.assign(data.metrics, overlay.metrics || {});
    const theme = data.themes[overlay.theme];
    const section = (theme.sections || []).find(item => item.key === overlay.section);
    if (!section) return data;

    section.label = overlay.sectionLabel || section.label;
    section.description = overlay.sectionDescription || section.description;
    const additions = overlay.metricOrder || [];
    section.metrics = [...section.metrics.filter(key => !additions.includes(key)), ...additions];
    theme.metrics = theme.sections.flatMap(item => item.metrics || []);
    data.version = overlay.versionLabel || data.version;
    data.updated = overlay.updatedLabel || data.updated;
    return data;
  }

  globalThis.fetch = async (input, init) => {
    const response = await nativeFetch(input, init);
    if (!response.ok || !isSiteDataRequest(input)) return response;
    try {
      const [data, overlayResponse] = await Promise.all([
        response.clone().json(),
        nativeFetch(overlayUrl, { cache: 'no-store' })
      ]);
      if (!overlayResponse.ok) return response;
      const overlay = await overlayResponse.json();
      const merged = mergeDraft(data, overlay);
      const headers = new Headers(response.headers);
      headers.set('content-type', 'application/json; charset=utf-8');
      return new Response(JSON.stringify(merged), {
        status: response.status,
        statusText: response.statusText,
        headers
      });
    } catch (error) {
      console.warn('Overlay Agricoltura II non applicato', error);
      return response;
    }
  };
})();
