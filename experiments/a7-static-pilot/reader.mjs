// Browser-compatible ES module. No network, engine port, model or DOM dependency.
const copy = value => JSON.parse(JSON.stringify(value));
const normalize = text => text.normalize('NFKC').replace(/[’‘]/gu, "'").trim().replace(/[?.!\s]+$/u, '').replace(/\s+/gu, ' ').toLocaleLowerCase('it');
const freeze = value => { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; };

export async function loadPilot(text, trustedRelease) {
  if (typeof text !== 'string' || !trustedRelease || trustedRelease.schemaVersion !== 1) throw new Error('invalid_release');
  for (const key of ['bundleSha256', 'catalogSha256', 'engineSha256', 'programSha256', 'casesSha256', 'scopeSha256', 'builderSha256', 'readerSha256']) {
    if (!/^[a-f0-9]{64}$/u.test(trustedRelease[key] || '')) throw new Error('invalid_release_hash');
  }
  trustedRelease = freeze(copy(trustedRelease));
  const bytes = new TextEncoder().encode(text);
  const digest = Array.from(new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256', bytes)), n => n.toString(16).padStart(2, '0')).join('');
  if (digest !== trustedRelease.bundleSha256 || bytes.length !== trustedRelease.bundleBytes) throw new Error('bundle_integrity_mismatch');
  const bundle = JSON.parse(text);
  if (bundle.schemaVersion !== 1) throw new Error('unsupported_schema');
  for (const key of ['catalogSha256', 'engineSha256', 'programSha256', 'casesSha256', 'scopeSha256', 'builderSha256', 'readerSha256']) {
    if (bundle[key] !== trustedRelease[key]) throw new Error('stale_release:' + key);
  }
  const questions = new Map();
  for (const q of bundle.questions) {
    if (questions.has(q.id) || !['supported', 'partially_supported', 'not_determinable'].includes(q.classification)) throw new Error('invalid_question');
    for (const cid of [...q.requiredCaseRefs, ...q.contextCaseRefs]) if (!Object.hasOwn(bundle.cases, cid)) throw new Error('missing_case');
    questions.set(q.id, q);
  }
  freeze(bundle);
  const choices = dossierId => bundle.questions.filter(q => !dossierId || q.dossierId === dossierId).map(q => ({ questionId: q.id, question: q.question, dossierId: q.dossierId }));
  const boundary = (resolution, reason, dossierId) => ({ schemaVersion: 1, resolution, reason, choices: choices(dossierId) });
  function resolve(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input) || ![Object.prototype, null].includes(Object.getPrototypeOf(input))) return boundary('invalid_request', 'request_object_required');
    const allowed = ['question', 'questionId', 'caseId', 'dossierId', 'approvedPartial'];
    if (Object.keys(input).some(k => !allowed.includes(k))) return boundary('invalid_request', 'unexpected_request_field');
    const modes = ['question', 'questionId', 'caseId'].filter(k => Object.hasOwn(input, k));
    if (modes.length !== 1 || typeof input[modes[0]] !== 'string' || !input[modes[0]].trim() || input[modes[0]].length > 2048) return boundary('invalid_request', 'one_bounded_selection_required');
    if (Object.hasOwn(input, 'approvedPartial') && typeof input.approvedPartial !== 'boolean') return boundary('invalid_request', 'partial_consent_must_be_boolean');
    if (Object.hasOwn(input, 'dossierId') && (typeof input.dossierId !== 'string' || !choices(input.dossierId).length)) return boundary('out_of_scope', 'dossier_not_in_pilot');
    let q, ids, classification;
    if (modes[0] === 'caseId') {
      if (!Object.hasOwn(bundle.cases, input.caseId)) return boundary('out_of_scope', 'case_not_precomputed', input.dossierId);
      if (input.dossierId && !bundle.questions.some(q => q.dossierId === input.dossierId && [...q.requiredCaseRefs, ...q.contextCaseRefs].includes(input.caseId))) return boundary('out_of_scope', 'case_outside_dossier', input.dossierId);
      ids = [input.caseId]; classification = bundle.cases[input.caseId].response.status;
    } else {
      const matches = modes[0] === 'questionId' ? [questions.get(input.questionId)].filter(Boolean) : bundle.questions.filter(q => normalize(q.question) === normalize(input.question));
      const scoped = matches.filter(q => !input.dossierId || q.dossierId === input.dossierId);
      if (scoped.length !== 1) return boundary(modes[0] === 'questionId' ? 'out_of_scope' : 'needs_clarification', 'select_a_verified_question', input.dossierId);
      q = scoped[0]; ids = [...q.requiredCaseRefs, ...q.contextCaseRefs]; classification = q.classification;
    }
    const partial = ids.filter(cid => bundle.cases[cid].query.allowPartial === true);
    if (partial.length && input.approvedPartial !== true) return { ...boundary('needs_confirmation', 'partial_coverage_requires_explicit_consent', q?.dossierId), affectedCaseIds: partial };
    return copy({ schemaVersion: 1, resolution: 'resolved', classification,
      cacheKey: `${digest}/${modes[0]}/${q?.id || input.caseId}/${input.approvedPartial === true}`,
      release: trustedRelease, questionPlan: q || null,
      components: ids.map(cid => ({ caseId: cid, ...bundle.cases[cid] })),
      limits: bundle.limits });
  }
  return Object.freeze({ resolve, describe: () => copy({ release: trustedRelease, choices: choices(), limits: bundle.limits }) });
}
