// Experimental transport only: values and refusals are produced by A6 at build time.
const copy = x => JSON.parse(JSON.stringify(x));
const plain = x => x !== null && typeof x === 'object' && !Array.isArray(x) && [Object.prototype, null].includes(Object.getPrototypeOf(x));
const hashPattern = /^[a-f0-9]{64}$/u;
const textEncoder = new TextEncoder();
const canonical = x => {
  if (Array.isArray(x)) return '[' + x.map(canonical).join(',') + ']';
  if (plain(x)) return '{' + Object.keys(x).sort().map(k => JSON.stringify(k)+':'+canonical(x[k])).join(',') + '}';
  if (x === null || ['string', 'boolean'].includes(typeof x) || (typeof x === 'number' && Number.isFinite(x))) return JSON.stringify(x);
  throw new Error('invalid_json_value');
};
const sha = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
const freeze = x => { if (x && typeof x === 'object') { Object.values(x).forEach(freeze); Object.freeze(x); } return x; };
const ROOT_LIMIT = 2 * 1024 * 1024;
const PACKED_LIMIT = 8 * 1024 * 1024;
const RAW_LIMIT = 16 * 1024 * 1024;

async function boundedBytes(stream, limit) {
  if (!stream) throw new Error('missing_body');
  const reader = stream.getReader(); const chunks = []; let length = 0;
  try {
    while (true) {
      const {done, value} = await reader.read(); if (done) break;
      length += value.length;
      if (length > limit) { await reader.cancel(); throw new Error('artifact_byte_budget'); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const out = new Uint8Array(length); let offset = 0;
  for (const chunk of chunks) { out.set(chunk, offset); offset += chunk.length; }
  return out;
}

export async function openRuntime(releaseText, trustedReleaseSha256, baseURL, {fetcher=globalThis.fetch}={}) {
  // Trust anchor is supplied by the embedding release, never read from the payload itself.
  if (typeof releaseText !== 'string' || !hashPattern.test(trustedReleaseSha256 || '')) throw new Error('invalid_release');
  const rootBytes = textEncoder.encode(releaseText);
  if (rootBytes.length > ROOT_LIMIT || await sha(rootBytes) !== trustedReleaseSha256) throw new Error('release_integrity_mismatch');
  const root = freeze(JSON.parse(releaseText));
  if (root.schemaVersion !== 1 || root.kind !== 'a7-selective-query-runtime' || !Array.isArray(root.metrics)) throw new Error('invalid_release_schema');
  for (const key of ['catalogSha256','engineSha256','workbenchSha256','builderSha256','readerSha256']) {
    if (!hashPattern.test(root[key] || '')) throw new Error('invalid_release_hash');
  }
  const base = new URL(baseURL, globalThis.location?.href);
  if (!['http:', 'https:'].includes(base.protocol) || base.origin !== globalThis.location?.origin || !base.pathname.endsWith('/')) throw new Error('same_origin_directory_required');
  const summaries = new Map(root.metrics.map(m => [m.metric,m]));
  if (summaries.size !== root.metrics.length) throw new Error('duplicate_metric');
  // Bounded cache: loaded responses from a different release can never leak into this instance.
  const cache = new Map();
  let cacheBytes = 0;
  async function load(ref) {
    if (!plain(ref) || !hashPattern.test(ref.sha256 || '') || ref.path !== ref.sha256+'.json.gz' ||
        !hashPattern.test(ref.rawSha256 || '') || !Number.isInteger(ref.bytes) || ref.bytes <= 0 || ref.bytes > PACKED_LIMIT ||
        !Number.isInteger(ref.rawBytes) || ref.rawBytes <= 0 || ref.rawBytes > RAW_LIMIT) throw new Error('invalid_artifact_reference');
    if (cache.has(ref.sha256)) return cache.get(ref.sha256).value;
    const response = await fetcher(new URL(ref.path, base).href, {credentials:'omit', redirect:'error'});
    if (!response.ok) throw new Error('artifact_fetch_failed');
    const packed = await boundedBytes(response.body, ref.bytes);
    if (packed.length !== ref.bytes || await sha(packed) !== ref.sha256) throw new Error('artifact_integrity_mismatch');
    const raw = await boundedBytes(new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip')), ref.rawBytes);
    if (raw.length !== ref.rawBytes || await sha(raw) !== ref.rawSha256) throw new Error('artifact_integrity_mismatch');
    const value = freeze(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)));
    if (value.schemaVersion !== 1) throw new Error('invalid_artifact_schema');
    while (cache.size && (cache.size >= 8 || cacheBytes + ref.rawBytes > RAW_LIMIT)) {
      const key = cache.keys().next().value;
      cacheBytes -= cache.get(key).bytes; cache.delete(key);
    }
    cache.set(ref.sha256, {value, bytes:ref.rawBytes}); cacheBytes += ref.rawBytes;
    return value;
  }
  async function detail(metric) {
    if (!summaries.has(metric)) throw new Error('unknown_metric');
    const value = await load(summaries.get(metric).detail);
    if (value.metric !== metric) throw new Error('artifact_selection_mismatch');
    return value;
  }
  async function run(plan, {approvedPartial=false}={}) {
    // Snapshot before any await. Caller state may be reused during a fetch;
    // selection, returned plan and digest must refer to the same private JSON.
    if (!plain(plan)) throw new Error('invalid_plan');
    const planText = canonical(plan);
    if (textEncoder.encode(planText).length > 100000 || typeof approvedPartial !== 'boolean') throw new Error('invalid_plan');
    plan = JSON.parse(planText);
    // Validate the complete plan before any fetch; no implicit consent or query rewriting.
    if (!plain(plan) || Object.keys(plan).sort().join(',') !== 'schemaVersion,steps' || plan.schemaVersion !== 1 ||
        !Array.isArray(plan.steps) || !plan.steps.length || plan.steps.length > 32) throw new Error('invalid_plan');
    const ids = new Set();
    for (const step of plan.steps) {
      if (!plain(step) || Object.keys(step).sort().join(',') !== 'id,request' || typeof step.id !== 'string' ||
          !/^[A-Za-z0-9_-]{1,80}$/u.test(step.id) || ids.has(step.id) || !plain(step.request)) throw new Error('invalid_step');
      ids.add(step.id);
      if (step.request.allowPartial === true && !approvedPartial) return {resolution:'needs_confirmation',reason:'partial_coverage_requires_explicit_consent'};
    }
    const components = [];
    for (const step of plan.steps) {
      const request = step.request;
      const selector = request.selectors?.length === 1 && request.selectors[0];
      if (!plain(selector) || !summaries.has(selector.metric)) return {resolution:'not_materialized',reason:'request_outside_static_envelope',stepId:step.id};
      const data = await detail(selector.metric);
      const view = data.views.find(v => v.dimension === selector.dimension);
      const profile = ({observe:'current',lookup:'current',compare:'comparison',series:'history',rank:'ranking',benchmark_gap:'benchmark',weighted_ratio:'aggregation'})[request.operation];
      const ref = view?.shards[profile];
      if (!ref) return {resolution:'not_materialized',reason:'request_outside_static_envelope',stepId:step.id};
      const shard = await load(ref);
      if (shard.metric !== selector.metric || shard.dimension !== selector.dimension || shard.profile !== profile) throw new Error('artifact_selection_mismatch');
      const match = shard.entries.find(e => canonical(e.request) === canonical(request));
      if (!match) return {resolution:'not_materialized',reason:'request_outside_static_envelope',stepId:step.id};
      const r = match.response;
      // Consent also protects numeric observations retained in an A6 refusal.
      const c = r.coverage;
      const partial = r.reasons?.includes('partial_coverage_requires_opt_in') ||
        (c?.usable > 0 && c.usable < c.requested && r.observations?.some(o => Number.isFinite(o.value)));
      if (partial && !approvedPartial) return {resolution:'needs_confirmation',reason:'partial_coverage_requires_explicit_consent',stepId:step.id};
      components.push({id:step.id,response:r});
    }
    const computed = components.filter(s => s.response.status === 'computed').length;
    return copy({resolution:'resolved', schemaVersion:1, plan, planSha256:await sha(textEncoder.encode(planText)),
      workbenchSha256:root.workbenchSha256,catalogSha256:root.catalogSha256,
      status:computed===components.length?'computed_components':computed?'mixed_components':'refused_components',
      interpretationStatus:'not_assessed',steps:components});
  }
  return Object.freeze({discover: async metric => copy(metric===undefined ? root : await detail(metric)), run});
}
