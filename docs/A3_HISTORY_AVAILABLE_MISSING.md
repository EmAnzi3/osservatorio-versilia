# A3 historical-series acquisition workstream

This stacked workstream starts from PR #302 and targets only A3 pairs where:

- \`dimension == serie_storica\`
- \`state == AVAILABLE_MISSING\`

Initial certified baseline: **83 pairs across 34 source profiles**.

## Operating rule

Work source-profile first, not metric-by-metric. Each acquisition batch must:

1. derive its target pairs from the effective A3 matrix;
2. use official/source-backed data already identified by A3 evidence;
3. materialize canonical public history data;
4. turn the affected matrix pairs from \`AVAILABLE_MISSING\` to \`ACQUIRED\`;
5. pass the publication contract so \`ACQUIRED\` cannot remain non-public;
6. never redesign A5 surfaces.

The workflow artifact is the live backlog. The branch is complete only when the historical AVAILABLE_MISSING count reaches zero or a pair is reclassified with documented evidence because the original A3 availability assessment was wrong.
