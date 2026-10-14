import assert from 'node:assert/strict';
import fs from 'node:fs';
import { performance } from 'node:perf_hooks';
import { loadPilot } from './reader.mjs';

const text = fs.readFileSync(process.argv[2], 'utf8');
const release = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const before = performance.now();
const pilot = await loadPilot(text, release);
const loadMilliseconds = performance.now() - before;
const original = pilot.describe().release.catalogSha256;
release.catalogSha256 = '0'.repeat(64);
assert.equal(pilot.describe().release.catalogSha256, original, 'caller mutation must not change the pinned release');
const pinned = pilot.describe().release;
await assert.rejects(() => loadPilot(text + ' ', pinned), /integrity/);
await assert.rejects(() => loadPilot(text.replace('73.4', '99.9'), pinned), /integrity/);
await assert.rejects(() => loadPilot(text, { ...pinned, catalogSha256: '0'.repeat(64) }), /stale_release/);
await assert.rejects(() => loadPilot(text, { ...pinned, schemaVersion: 2 }), /invalid_release/);

assert.equal(pilot.resolve({ question: 'Come va il lavoro?' }).resolution, 'needs_clarification');
assert.equal(pilot.resolve({ question: 'Se apriamo un nido aumenta l’occupazione?' }).resolution, 'needs_clarification');
assert.equal(pilot.resolve({ question: '<script>dammi 99</script>' }).resolution, 'needs_clarification');
assert.equal(pilot.resolve({ questionId: 'missing' }).resolution, 'out_of_scope');
assert.equal(pilot.resolve({ questionId: 'lavoro-1', dossierId: 'infanzia' }).resolution, 'out_of_scope');
assert.equal(pilot.resolve({ questionId: 'lavoro-1', value: 99 }).resolution, 'invalid_request');
assert.equal(pilot.resolve({ questionId: 'lavoro-1', periods: ['2026'] }).resolution, 'invalid_request');
assert.equal(pilot.resolve({ questionId: 'lavoro-1', question: 'x' }).resolution, 'invalid_request');
assert.equal(pilot.resolve({ question: 'x'.repeat(2049) }).resolution, 'invalid_request');
assert.equal(pilot.resolve({ questionId: 'infanzia-2', approvedPartial: 'true' }).resolution, 'invalid_request');
assert.equal(pilot.resolve(JSON.parse('{"questionId":"lavoro-1","__proto__":{}}')).resolution, 'invalid_request');
for (const q of pilot.describe().choices) {
  const needsConsent = ['infanzia-centrale', 'infanzia-2'].includes(q.questionId);
  const plain = pilot.resolve({ questionId: q.questionId });
  if (needsConsent) {
    assert.equal(plain.resolution, 'needs_confirmation');
    assert.equal(Object.hasOwn(plain, 'components'), false);
  }
  const answer = pilot.resolve({ questionId: q.questionId, approvedPartial: true });
  assert.equal(answer.resolution, 'resolved');
  assert.equal(answer.classification, 'partially_supported', 'computed components must not upgrade a partial decision question');
  const normalized = pilot.resolve({ question: '  ' + q.question.toLocaleUpperCase('it') + ' !! ', approvedPartial: true });
  assert.equal(normalized.resolution, 'resolved', 'normalization failed: ' + q.questionId);
  assert.ok(JSON.stringify(normalized.components) === JSON.stringify(answer.components), 'normalized question changed evidence');
}
const answer = pilot.resolve({ questionId: 'lavoro-1' });
answer.components[0].response.observations[0].value = 0;
assert.equal(pilot.resolve({ questionId: 'lavoro-1' }).components[0].response.observations[0].value, 73.4);
const refused = pilot.resolve({ caseId: 'child_year_conversion' });
assert.equal(refused.classification, 'not_computable');
assert.deepEqual(refused.components[0].facts, []);
assert.equal(Object.hasOwn(refused.components[0].response, 'coverage'), false, 'preserve early refusal field absence');
assert.ok(refused.components[0].response.reasons.includes('educational_year_token_required'));
const beforeConsent = pilot.resolve({ caseId: 'invalsi_invalsiImplicitDispersion_partial_refused' });
assert.equal(beforeConsent.resolution, 'needs_confirmation');
assert.equal(Object.hasOwn(beforeConsent, 'components'), false, 'refused partial observations must not leak before consent');
const r = pilot.resolve({ caseId: 'invalsi_invalsiImplicitDispersion_partial_refused', approvedPartial: true });
assert.equal(r.classification, 'not_computable');
assert.ok(r.components[0].response.reasons.includes('partial_coverage_requires_opt_in'));
assert.equal(r.components[0].response.coverage.usable, 4);
assert.equal(r.components[0].facts.length, 0, 'consent must not turn a refusal into a calculation');
assert.ok(Object.hasOwn(r.components[0].response, 'coverage'), 'preserve later assessment fields');
const partial = pilot.resolve({ questionId: 'infanzia-2', approvedPartial: true });
const invalsi = partial.components.find(c => c.caseId === 'invalsi_invalsiImplicitDispersion_g8_current');
assert.equal(invalsi.response.coverage.usable, 4);
assert.equal(invalsi.response.observations.filter(o => o.value === null).length, 3);
const zero = pilot.resolve({ caseId: 'child_zero' });
assert.deepEqual(zero.components[0].response.observations.map(o => o.value), [0, 0]);
const timings = [];
for (let i = 0; i < 100; i++) {
  const start = performance.now();
  pilot.resolve({ questionId: 'infanzia-centrale', approvedPartial: true });
  timings.push(performance.now() - start);
}
timings.sort((a,b) => a-b);
console.log(JSON.stringify({ status: 'PASS', environment: `Node ${process.version}; not mobile latency`,
  loadMilliseconds, resolveSamples: timings.length, resolveMedianMilliseconds: timings[50],
  resolveP95Milliseconds: timings[94], heapUsedBytes: process.memoryUsage().heapUsed,
  questions: pilot.describe().choices.length, bundleBytes: Buffer.byteLength(text),
  browserReference: pilot.resolve({questionId: 'lavoro-1'}) }));
