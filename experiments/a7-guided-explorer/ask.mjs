import { units } from './explorer.mjs';

// Interprete statico delle domande in italiano: traduce una domanda nella stessa
// selezione del modulo «Una misura» (indicatore, dettaglio, lettura, Comune,
// riferimento) o in un incrocio rivisto. Non calcola nulla: i numeri restano del
// motore A6. Un futuro livello LLM dovrà produrre la stessa struttura `selection`.

const STOP = new Set(('a ad al alla alle allo agli ai all che chi ci come con cosa cos cui da dal dalla dalle dai degli dei del della delle dello di e ed fra gli ha hanno ho i il in la le lo ma mi ne nei nel nella nelle nello noi o per piu po qual quale quali quanta quante quanti quanto se si sono su sul sulla sulle sui tra tu un una uno vs ce c e è dimmi mostrami fammi vedere sapere vorrei voglio dati dato valore valori numero comune comuni versilia sette territorio oggi ora anno anni ultimo ultima ultimi recente attuale negli sugli dagli agli coi col tutti tutte tutto tanto tanti molto meno avere essere esiste ci sono costa costano paga pagano fa fanno fra tra rispetto vive vivono abita abitano spende spendono qual quali dove invece anche mentre allora stesso stessa stessi stesse quello quella quelli ok grazie poi pure dieci cinque venti trenta quindici fa vanno va vengono andare venire produce producono economica economico economiche economici cara caro care cari').split(' '));

// Parole della domanda che indicano la lettura; l'ordine conta (prima vince).
const OPERATIONS = [
  ['anomaly', /\b(fuori scala|anomal\w*|outlier|valori estremi|valore estremo)\b/],
  ['benchmark_gap', /\b(toscana|italia|regional\w*|nazional\w*|media (?:della )?(?:toscana|regione|italia))\b/],
  ['trend', /\b(tendenz\w*|trend|pendenz\w*)\b/],
  ['percentage_points', /\bpunti percentuali\b/],
  ['series', /\b(nel tempo|negli anni|andamento|evoluzion\w*|stori\w*|serie|anno per anno|dal \d{4}|com e cambiat\w*|anni fa|in passato)\b/],
  ['relative_change', /\b(in percentuale|percentualmente|di quanto (?:e )?(?:cresciut|aumentat|calat|diminuit)\w*|variazione percentuale|quanto (?:e )?(?:cresciut|aumentat|calat|diminuit|cambiat|variat)\w*|crescit\w*|aument\w*|cal\w* |diminu\w*|variazion\w*|cambiat\w*)\b/],
  ['rank', /\b(classifica|ordin\w*|piu alt\w*|piu bass\w*|il piu|la piu|i piu|le piu|maggior\w*|minor\w*|primo|prima posizione|ultimo posto|chi ha (?:piu|meno)|dove (?:e|sono|ci sono) (?:piu|meno)|di (?:piu|meno)|piu (?:vecch|giovan|ricc|pover|car|economic|popolos|grand|piccol)\w*|in testa|graduatori\w*|top|podio|(?:primo|ultimo|ultima|prima) (?:comune|posto|in classifica)|chi (?:fa|va) (?:meglio|peggio))\b/],
  ['compare', /\b(confront\w*|paragon\w*|rispetto agli altri|fra i comuni|tra i comuni|tutti i comuni|gli altri comuni|altri comuni|sette comuni|differenz[ae]|ogni comune|ciascun comune|contro|vs|versus)\b/],
  ['weighted_ratio', /\b(versilia nel suo insieme|intera versilia|tutta la versilia|complessivo della versilia|totale della versilia|in versilia)\b/],
];
const ASSOCIATION = /\b(relazion\w*|legat\w*|legame|correlaz\w*|associazione (?:tra|fra)|incroci\w*|dipend\w* da|influenz\w*|va di pari passo|quando .* (?:anche|allora))\b/;

// Sinonimi d'uso comune → parole che compaiono nelle etichette del catalogo.
const SYNONYMS = {
  abitanti: 'popolazione residenti', abitante: 'residenti', residenti: 'popolazione', gente: 'popolazione', persone: 'popolazione',
  stipendi: 'reddito', stipendio: 'reddito', guadagni: 'reddito', guadagna: 'reddito', guadagnano: 'reddito', ricchezza: 'reddito', ricchi: 'reddito', poveri: 'reddito vulnerabilita',
  case: 'abitazioni immobiliare', casa: 'abitazioni immobiliare', affitti: 'locazione affitto', affitto: 'locazione', prezzi: 'quotazioni prezzo', mattone: 'immobiliare',
  vecchi: 'vecchiaia anziani', anziani: 'vecchiaia anziani', invecchiamento: 'vecchiaia', giovani: 'giovani', bambini: 'infanzia minori', figli: 'natalita nascite',
  nati: 'nascite natalita', nascono: 'nascite natalita', nascite: 'nascite natalita', nasce: 'nascite', morti: 'decessi', stranieri: 'stranieri cittadinanza', immigrati: 'stranieri',
  lavoro: 'occupazione', lavorano: 'occupazione occupati', disoccupati: 'disoccupazione', disoccupazione: 'disoccupazione', donne: 'femminile', uomini: 'maschile',
  aziende: 'unita locali', imprese: 'unita locali', ditte: 'imprese', negozi: 'unita locali commercio', dipendenti: 'addetti', lavoratori: 'addetti',
  turisti: 'turismo presenze arrivi', arrivano: 'arrivi', arriva: 'arrivi', turismo: 'turistico presenze', alberghi: 'ricettiva strutture', letti: 'posti letto',
  spazzatura: 'rifiuti', immondizia: 'rifiuti', raccolta: 'differenziata rifiuti', riciclo: 'differenziata', ricicla: 'differenziata', riciclano: 'differenziata',
  vuote: 'occupate', sfitte: 'occupate', restano: 'permanenza', laureati: 'terziario titolo', laurea: 'terziario titolo', inquinanti: 'euro', colonnine: 'ricarica punti', piste: 'percorsi', ottica: 'ftth', veloce: 'ftth banda', fondi: 'risorse', superficie: 'superficie',
mare: 'balneazione costa', spiagge: 'balneazione spiagge concessioni', balneari: 'concessioni demaniali',
  famiglia: 'famiglie persone', famiglie: 'persone', tasse: 'tributi imposte irpef imu tari', imu: 'imu', tari: 'tari rifiuti', irpef: 'irpef addizionale',
  istruzione: 'diploma titolo', studio: 'diploma titolo', scuole: 'scuola scolastici istruzione', scuola: 'scolastici istruzione', studenti: 'alunni', alunni: 'alunni', mensa: 'mense', diploma: 'diploma titolo',
  ospedale: 'ospedalieri ricoveri', medici: 'medici sanita', farmacie: 'farmacie', salute: 'sanitari salute',
  auto: 'autovetture motorizzazione', macchine: 'autovetture motorizzazione', traffico: 'veicoli', autobus: 'tpl trasporto pubblico', bus: 'tpl', treni: 'ferroviario',
  internet: 'banda ultralarga ftth', fibra: 'ftth fibra', connessione: 'ftth',
  benzina: 'carburanti benzina', gasolio: 'carburanti gasolio', diesel: 'gasolio', carburante: 'carburanti',
  frane: 'frana', alluvioni: 'alluvione idraulica', caldo: 'temperatura', pioggia: 'precipitazioni', clima: 'temperatura precipitazioni',
  debito: 'debito', spesa: 'spesa impegnata', bilancio: 'spesa entrate', pnrr: 'pnrr', opere: 'opere',
  biblioteche: 'bibliotecari prestiti', libri: 'prestiti bibliotecari', cultura: 'cultura', sport: 'sport',
  verde: 'verde', boschi: 'forestale bosco', suolo: 'suolo consumato', cemento: 'consumo suolo',
};

// Parole generiche: da sole non bastano a scegliere un indicatore.
const GENERIC = new Set(['base', 'medio', 'media', 'medi', 'totale', 'tasso', 'numero', 'quota', 'indice', 'livello', 'percentuale', 'mille', 'abitante', 'residenti', 'spesa', 'costo', 'prezzo', 'qualita', 'servizi', 'servizio'].map(w => w.length > 4 ? w.replace(/[aeiou]$/, '').slice(0, 6) : w));

// Concetti frequenti → indicatore principale, se presente nel runtime.
const CONCEPTS = { abitanti: 'population', residenti: 'population', popolazione: 'population', imprese: 'localUnits', aziende: 'localUnits', ditte: 'localUnits', reddito: 'income', redditi: 'income', stipendi: 'income', anziani: 'oldAgeIndex', vecchiaia: 'oldAgeIndex', stranieri: 'foreignResidents', disoccupazione: 'unemploymentRate', disoccupati: 'unemploymentRate', turisti: 'tourismPresences', presenze: 'tourismPresences', differenziata: 'recycling', rifiuti: 'wastePerResident', auto: 'motorization', macchine: 'motorization', nascite: 'naturalDemographicDynamics', arrivano: 'tourismArrivals', arrivi: 'tourismArrivals', nascono: 'naturalDemographicDynamics', case: 'omiResidential', affitti: 'omiResidential', vuote: 'vacantHomes', sfitte: 'vacantHomes', lavorano: 'employmentRate', turismo: 'tourismPresences', ricicla: 'recycling', riciclano: 'recycling', negozi: 'localUnits', superficie: 'municipalSurface', scuole: 'schoolSites', laureati: 'tertiary', restano: 'tourismAverageStay', permanenza: 'tourismAverageStay', uscita: 'outboundCommuters', entrata: 'inboundCommuters' };

// Espressioni di più parole riscritte prima dell'analisi.
const PHRASES = [
  [/\b(non lavorano|senza lavoro|senza un lavoro)\b/g, 'disoccupati'],
  [/\bseconde case\b/g, 'abitazioni non occupate'],
  [/\bcosto (?:dei rifiuti|della raccolta|del servizio rifiuti|della spazzatura)\b/g, 'costo servizio rifiuti'],
  [/\b(?:spend\w*|spesa) (?:\w+ )?per (?:la |le )?scuol\w*\b/g, 'spesa istruzione diritto studio'],
  [/\b(?:piu|meno) vecch\w*\b/g, m => 'indice di vecchiaia ' + (m.startsWith('piu') ? 'piu alto' : 'piu basso')],
  [/\b(?:piu|meno) giovan\w*\b/g, m => 'indice di vecchiaia ' + (m.startsWith('piu') ? 'piu basso' : 'piu alto')],
  [/\b(?:piu|meno) anzian[oa]\b/g, m => 'indice di vecchiaia ' + (m.startsWith('piu') ? 'piu alto' : 'piu basso')],
  [/\b(?:piu|meno) popolos\w*\b/g, m => 'popolazione ' + (m.startsWith('piu') ? 'piu alto' : 'piu basso')],
  [/\b(?:piu|meno) (?:estes|vast)\w*\b|\b(?:piu|meno) (?:grand|piccol)\w* per (?:superficie|estensione|territorio)\b/g, m => 'superficie comunale ' + (/^piu (?:estes|vast|grand)|^meno piccol/.test(m) ? 'piu alto' : 'piu basso')],
  [/\b(?:piu|meno) (?:grand|piccol)\w*\b/g, m => 'popolazione ' + (/^piu grand|^meno piccol/.test(m) ? 'piu alto' : 'piu basso')],
  [/\b(?:si vive|vivono|campano) (?:di )?(?:piu|meno)\b|\b(?:vita media|longevit\w*)\b/g, m => 'speranza di vita ' + (/meno/.test(m) ? 'piu basso' : 'piu alto')],
  [/\b(?:prezz\w*|cost\w*|quotazion\w*|valor\w*) (?:delle |della |di )?(?:case|casa|abitazion\w*)\b|\bcase cost\w*|\bcostano (?:di )?(?:piu|meno) (?:le )?case\b/g, m => 'quotazioni immobiliari ' + (/meno/.test(m) ? 'piu basso' : (/piu/.test(m) ? 'piu alto' : ''))],
  [/\bescono (?:dal comune )?per lavor\w*\b/g, 'pendolari in uscita'],
  [/\bentrano (?:nel comune )?per lavor\w*\b/g, 'pendolari in entrata'],
];
const rewrite = text => PHRASES.reduce((t, [re, to]) => t.replace(re, to), text);

// Nomi brevi e d'uso dei Comuni.
const TOWN_ALIASES = { forte: 'Forte dei Marmi', 'forte dei marmi': 'Forte dei Marmi', viareggio: 'Viareggio', camaiore: 'Camaiore', massarosa: 'Massarosa', pietrasanta: 'Pietrasanta', seravezza: 'Seravezza', stazzema: 'Stazzema' };

export function normalize(text) {
  return String(text || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[’'`\u2010-\u2015-]/g, ' ').replace(/[^a-z0-9.,%\s]/g, ' ').replace(/\s+/g, ' ').trim();
}

// Radice leggera: le prime 6 lettere bastano a unire singolare/plurale e derivati.
const stem = word => { const w = word.length > 4 ? word.replace(/[aeiou]$/, '') : word; return w.length > 6 ? w.slice(0, 6) : w; };
const tokens = text => normalize(text).split(' ').filter(w => w.length > 1 && !STOP.has(w));

function expand(words) {
  const out = [];
  for (const word of words) { out.push(word); if (SYNONYMS[word]) out.push(...SYNONYMS[word].split(' ')); }
  return out;
}

// L'indice è costruito in fase di build dal catalogo e dal runtime pubblicato.
export function prepare(index) {
  const df = new Map();
  const docs = index.metrics.map(metric => {
    const fields = [[metric.label, 3], [metric.short, 3], [(metric.terms || []).join(' '), 2.5], [metric.section, 1], [metric.themeLabel, 0.8], [metric.description, 0.6]];
    const weights = new Map();
    for (const [text, weight] of fields) for (const word of tokens(text)) {
      const s = stem(word); weights.set(s, Math.max(weights.get(s) || 0, weight));
    }
    for (const s of weights.keys()) df.set(s, (df.get(s) || 0) + 1);
    return { metric, weights, labelStems: new Set(tokens(metric.label + ' ' + metric.short).map(stem)),
      termStems: new Set(tokens([metric.label, metric.short, (metric.terms || []).join(' '), metric.section].join(' ')).map(stem)),
      viewStems: new Set(tokens((metric.views || []).map(v => v.label).join(' ')).map(stem)) };
  });
  const n = docs.length;
  for (const doc of docs) for (const [s, w] of doc.weights) doc.weights.set(s, w * Math.log(1 + n / df.get(s)));
  return { ...index, docs };
}

function findTowns(text, index) {
  const found = [];
  for (const [alias, name] of Object.entries(TOWN_ALIASES).sort((a, b) => b[0].length - a[0].length)) {
    const re = new RegExp('\\b' + alias + '\\b');
    if (re.test(text) && !found.some(t => t.name === name)) {
      const town = index.towns.find(t => t.name === name); if (town) found.push(town);
    }
  }
  return found;
}

function scoreMetrics(words, prepared) {
  const stems = [...new Set(expand(words).map(stem))];
  const concepts = new Set(words.map(w => CONCEPTS[w]).filter(Boolean));
  const numbers = words.filter(w => /^\d+$/.test(w) && w.length < 4);
  return prepared.docs.map(doc => {
    let score = 0, labelHits = 0, specific = 0;
    for (const s of stems) { const w = doc.weights.get(s); if (w) { score += GENERIC.has(s) ? w * 0.3 : w; if (doc.labelStems.has(s)) labelHits++; if (!GENERIC.has(s) && doc.termStems.has(s)) specific++; } }
    // Serve almeno una parola specifica nel nome o nei termini dell'indicatore.
    if (!specific) return { metric: doc.metric, score: 0 };
    // Le metriche il cui nome è coperto quasi tutto dalla domanda passano avanti.
    if (doc.labelStems.size) score *= 1 + labelHits / doc.labelStems.size;
    // A parità di parole, gli indicatori principali di ciascun tema vengono prima.
    if (doc.metric.featured) score *= 1.35;
    if (concepts.has(doc.metric.key)) score *= 1.6;
    // Età citate («20 e 34 anni») premiano gli indicatori con quel dettaglio.
    if (numbers.length && (doc.metric.views || []).some(v => numbers.every(n => (normalize(v.label).match(/\d+/g) || []).includes(n)))) score *= 1.5;
    return { metric: doc.metric, score, labelStems: doc.labelStems };
  }).filter(r => r.score > 0).sort((a, b) => b.score - a.score || a.metric.label.localeCompare(b.metric.label, 'it'));
}

// Età e sesso nominati nella domanda scelgono il dettaglio corrispondente.
function chooseView(top, words, text) {
  const views = top.metric.views || [];
  if (!views.length) return null;
  const asked = new Set(expand(words).map(stem));
  const women = /\b(donn\w*|femmin\w*)\b/.test(text), men = /\b(uomin\w*|maschi\w*)\b/.test(text);
  const young = /\b(giovan\w*|ragazz\w*|under)\b/.test(text), old = /\b(anzian\w*|over|pension\w*)\b/.test(text);
  const scored = views.map(v => {
    const label = normalize(v.label), ages = (label.match(/\d+/g) || []).map(Number);
    let hits = tokens(v.label).map(stem).filter(s => asked.has(s) && !top.labelStems.has(s) && !/^\d+$/.test(s)).length;
    hits += (normalize(text).match(/\d+/g) || []).filter(n => ages.includes(Number(n))).length;
    const ageAsked = young || old || /\d/.test(text);
    if (!ageAsked && ages.length) return { v, hits: 0, tie: 0 };
    if (young && ages.length && ages[0] < 25) hits += 1;
    if (old && ages.length && ages[0] >= 65) hits += 1;
    if (women && /\bdonne\b/.test(label) && !/uomini e donne/.test(label)) hits += 1;
    if (men && /\buomini\b/.test(label) && !/uomini e donne/.test(label)) hits += 1;
    // Senza sesso nella domanda, il dettaglio «uomini e donne» precede gli altri.
    const tie = !women && !men && /uomini e donne/.test(label) ? 0.5 : 0;
    return { v, hits, tie };
  }).filter(x => x.hits > 0).sort((a, b) => (b.hits + b.tie) - (a.hits + a.tie));
  return scored[0]?.v || null;
}

// Parole di età e sesso: scelgono il dettaglio, non l'indicatore.
const CUES = /^(giovan\w*|ragazz\w*|under|anzian\w*|over|donn\w*|femmin\w*|uomin\w*|maschi\w*|bambin\w*)$/;
// Con «donne» o «uomini» le età già implicite (nel nome o nel dettaglio precedente) restano.
const SEX = /\b(donn\w*|femmin\w*|uomin\w*|maschi\w*)\b/;
const ageContext = (text, label) => SEX.test(text) ? text + ' ' + (normalize(label).match(/\d+/g) || []).join(' ') : text;

function detectOperation(text) {
  for (const [operation, pattern] of OPERATIONS) if (pattern.test(text)) return operation;
  return null;
}

// Sceglie la lettura disponibile più vicina a quella chiesta.
function chooseOperation(wanted, metric, towns) {
  const ops = metric.operations;
  const has = op => ops.includes(op);
  const order = wanted ? [wanted] : [];
  if (wanted === 'relative_change') order.push('absolute_change', 'percentage_points', 'series');
  if (wanted === 'absolute_change') order.push('relative_change', 'series');
  if (wanted === 'percentage_points') order.push('absolute_change', 'series');
  if (wanted === 'trend') order.push('series');
  if (wanted === 'series') order.push('trend');
  if (wanted === 'weighted_ratio') order.push('compare');
  if (wanted === 'rank') order.push('compare');
  if (towns.length === 1) order.push('observe', 'lookup', 'compare');
  else order.push('compare', 'rank', 'observe');
  const chosen = order.find(has) || ops[0] || null;
  return { operation: chosen, exact: Boolean(wanted) && chosen === wanted };
}

const SINGLE_TOWN = new Set(['observe', 'lookup', 'series', 'trend', 'absolute_change', 'relative_change', 'percentage_points', 'benchmark_gap']);
// Domanda di seguito: comincia con «e…», «invece…», «anche…» o rimanda alla precedente.
const FOLLOW = /^(e|ed|invece|anche|mentre|allora|e invece|e per|e a|e nel|e in|e se|e per i|e per le)\b|\b(stesso|stessa|stessi|stesse|lo stesso|la stessa)\b/;

function stripQuestion(text) {
  let stripped = text;
  // I nomi dei Comuni non aiutano a scegliere l'indicatore.
  for (const alias of Object.keys(TOWN_ALIASES).sort((a, b) => b.length - a.length)) stripped = stripped.replace(new RegExp('\\b' + alias + '\\b', 'g'), ' ');
  // Neppure le parole che indicano la lettura (es. «fuori scala», «più alto»).
  for (const [, pattern] of OPERATIONS) stripped = stripped.replace(new RegExp(pattern.source, 'g'), ' ');
  return stripped.replace(new RegExp(ASSOCIATION.source, 'g'), ' ');
}

// Costruisce la selezione per un indicatore (ed eventuale dettaglio) già scelto.
function reading(result, metric, view, wanted, towns, text, previous) {
  const target = view ? { ...metric, view: view.dimension, operations: view.operations } : metric;
  // In una domanda di seguito senza lettura esplicita si conserva quella precedente,
  // salvo il caso di un Comune nominato dopo un confronto fra Comuni.
  let asked = wanted;
  if (!asked && previous) {
    const before = previous.selection.domanda;
    asked = towns.length && !SINGLE_TOWN.has(before) ? 'observe' : before;
  }
  const { operation, exact } = chooseOperation(asked, target, towns.length ? towns : (previous?.selection?.comune ? [{ code: previous.selection.comune }] : []));
  if (!operation) return { ...result, kind: 'no_reading', metric, alternatives: [] };
  if (wanted && !exact) result.notes.push('requested_reading_unavailable');
  let town = towns[0]?.code || null;
  if (!town && previous && SINGLE_TOWN.has(operation)) { town = previous.selection.comune || null; if (town) result.inherited.push('town'); }
  if (SINGLE_TOWN.has(operation) && !town) result.notes.push('town_needed');
  if (SINGLE_TOWN.has(operation) && towns.length > 1) result.notes.push('one_town_only');
  let benchmark = null;
  if (operation === 'benchmark_gap') benchmark = /\bitalia|nazional/.test(text) ? 'italy' : (previous?.selection?.riferimento && !/\btoscana|regional/.test(text) ? previous.selection.riferimento : 'tuscany');
  const selection = { indicatore: metric.key, dettaglio: target.view, domanda: operation };
  if (view) result.viewLabel = view.label;
  if (SINGLE_TOWN.has(operation)) selection.comune = town; // null: l'interfaccia chiede il Comune
  if (benchmark) selection.riferimento = benchmark;
  return { ...result, kind: 'reading', metric, selection, towns, wanted, alternatives: [] };
}

// Errori di battitura: una parola sconosciuta vicina a una del catalogo viene corretta
// («redito» → «reddito»). Distanza 1, oppure 2 per parole lunghe.
function distance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const row = [i]; let best = i;
    for (let j = 1; j <= b.length; j++) { row[j] = Math.min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); best = Math.min(best, row[j]); }
    if (best > max) return max + 1;
    prev = row;
  }
  return prev[b.length];
}
// Nomi dei Comuni scritti male («viaregio», «pietrasnta»).
const TOWN_WORDS = Object.keys(TOWN_ALIASES).filter(a => !a.includes(' ') && a.length > 5);
const fixTowns = text => text.split(' ').map(w => {
  if (w.length < 6 || TOWN_WORDS.includes(w)) return w;
  return TOWN_WORDS.find(a => a[0] === w[0] && distance(w, a, a.length >= 8 ? 2 : 1) <= (a.length >= 8 ? 2 : 1)) || w;
}).join(' ');
function correct(word, prepared) {
  if (word.length < 5 || /\d/.test(word)) return word;
  const vocab = vocabulary(prepared);
  if (!prepared.vocabSet) prepared.vocabSet = new Set(vocab);
  if (prepared.vocabSet.has(word) || prepared.docs.some(d => d.weights.has(stem(word)))) return word;
  const max = word.length >= 8 ? 2 : 1;
  let best = word, bestDistance = max + 1;
  for (const v of vocab) if (v[0] === word[0]) { const d = distance(word, v, max); if (d < bestDistance) { best = v; bestDistance = d; if (d === 1) break; } }
  return best;
}

// `previous`: l'ultima lettura riuscita della conversazione, per domande come «e a Camaiore?».
export function interpret(question, prepared, { metric: forced = null, previous = null } = {}) {
  const base = fixTowns(normalize(question)), text = rewrite(base);
  const result = { question, text, notes: [], inherited: [] };
  if (!text) return { ...result, kind: 'empty' };
  const prev = previous && previous.kind === 'reading' && previous.selection ? previous : null;
  const towns = findTowns(base, prepared);
  const words = tokens(stripQuestion(text)).map(w => correct(w, prepared));
  let wanted = detectOperation(text);
  // «Quale Comune ha più…», «Pietrasanta ha più abitanti di Camaiore?»: senza un solo Comune è un ordine.
  if ((!wanted || wanted === 'compare') && towns.length !== 1 && /\b(piu|meno|meglio|peggio)\b/.test(text) && !/\bdifferenz[ae]\b/.test(text)) wanted = 'rank';
  const cue = FOLLOW.test(text);
  const ranked = scoreMetrics(words, prepared);
  const content = words.filter(w => !GENERIC.has(stem(w)) && !/^\d+$/.test(w));
  // Copertura: quante parole specifiche della domanda trovano posto nell'indicatore.
  const coverage = r => {
    const doc = prepared.docs.find(d => d.metric === r.metric);
    const covered = content.filter(w => CUES.test(w) || [w, ...(SYNONYMS[w] || '').split(' ').filter(Boolean)].some(x => doc.termStems.has(stem(x)) || doc.viewStems.has(stem(x)))).length;
    return content.length ? covered / content.length : 1;
  };
  let top = ranked.length ? ((forced && ranked.find(r => r.metric.key === forced)) || ranked[0]) : null;
  if (top) {
    result.coverage = coverage(top);
    if (!forced && !ASSOCIATION.test(text) && content.length >= 2 && result.coverage <= 0.5) {
      // Il primo indicatore non copre la domanda: si prova fra i successivi più vicini.
      const better = ranked.slice(1, 6).find(r => r.score >= ranked[0].score * 0.25 && coverage(r) > 0.5);
      top = better || null;
      if (better) result.coverage = coverage(better);
    }
  }
  // Seguito della domanda precedente: stesso indicatore, cambia Comune, lettura o dettaglio.
  const prevMetric = prev && (prepared.metrics.find(m => m.key === prev.selection.indicatore) || prev.metric);
  const prevDoc = prevMetric && prepared.docs.find(d => d.metric.key === prevMetric.key);
  // «e le donne?»: la parola nuova è un dettaglio dell'indicatore precedente.
  const newView = prevDoc && content.length === 1 ? chooseView({ metric: prevMetric, labelStems: prevDoc.labelStems }, words, ageContext(text, prev.viewLabel || prevMetric.label)) : null;
  if (prevDoc && !forced && (!top || (cue && newView))) {
    const followable = towns.length || wanted || cue || /\b(toscana|italia)\b/.test(text);
    // Al più una parola nuova (per esempio «donne»): altrimenti è un'altra domanda.
    if (followable && (content.length === 0 || newView)) {
      result.followUp = true; result.inherited.push('metric');
      const keep = !newView && prev.selection.dettaglio !== prevMetric.view ? (prevMetric.views || []).find(v => v.dimension === prev.selection.dettaglio) : null;
      const view = newView || keep || null;
      return reading(result, prevMetric, view, wanted, towns, text, prev);
    }
  }
  if (!top) return { ...result, kind: 'no_metric', towns, near: ranked.slice(0, 3).map(r => r.metric) };
  const alternatives = ranked.filter(r => r !== top).slice(0, 3).filter(r => r.score >= ranked[0].score * 0.6).map(r => r.metric);

  // Incroci: due variabili e una parola di relazione.
  if (ASSOCIATION.test(text) && prepared.associations?.length) {
    const scores = new Map(ranked.map(r => [r.metric.key, r.score]));
    const best = prepared.associations.map(a => ({ a, score: Math.min(scores.get(a.left) || 0, scores.get(a.right) || 0) }))
      .filter(x => x.score > 0).sort((x, y) => y.score - x.score)[0];
    if (best) return { ...result, kind: 'association', association: best.a };
    return { ...result, kind: 'association_unavailable', metric: top.metric, alternatives };
  }

  // Un dettaglio (es. «15–24 anni», «femmine») vince sul dato complessivo se la domanda lo nomina.
  const view = chooseView(top, words, ageContext(text, top.metric.label));
  // «e il reddito?» dopo una domanda su un Comune: nuovo indicatore, stesso Comune e stessa lettura.
  const carry = prev && cue && !towns.length ? prev : null;
  if (carry) { result.followUp = true; }
  return { ...reading(result, top.metric, view, wanted, towns, text, carry), alternatives };
}

// Suggeritore: mentre si scrive propone domande complete che l'interprete capisce
// davvero. Ogni proposta è verificata con `interpret` prima di essere mostrata.
const lower = label => /^[A-Z]{2,}/.test(label) ? label : label.charAt(0).toLowerCase() + label.slice(1);
const TEMPLATES = {
  observe: (l, t) => t && `${l} a ${t}`,
  lookup: (l, t) => t && `${l} a ${t}`,
  series: (l, t) => t && `${l} a ${t} nel tempo`,
  benchmark_gap: (l, t) => t && `${l} a ${t} rispetto alla Toscana`,
  relative_change: (l, t) => t && `${l} a ${t}: variazione percentuale`,
  rank: (l, t) => !t && `Classifica dei Comuni: ${l}`,
  compare: (l, t) => !t && `${l}: confronto fra i Comuni`,
  weighted_ratio: (l, t) => !t && `${l} in tutta la Versilia`,
};
const ORDER_TOWN = ['observe', 'lookup', 'series', 'benchmark_gap', 'relative_change'];
const ORDER_ALL = ['rank', 'compare', 'weighted_ratio'];
const FOLLOW_UPS = [['series', 'E nel tempo?'], ['benchmark_gap', 'E rispetto alla Toscana?'], ['compare', 'E fra i sette Comuni?']];

function vocabulary(prepared) {
  if (prepared.vocab) return prepared.vocab;
  const words = new Map();
  const add = (w, n = 1) => { if (w.length > 2 && !/^\d+$/.test(w)) words.set(w, (words.get(w) || 0) + n); };
  for (const m of prepared.metrics) for (const w of tokens([m.label, m.short, (m.terms || []).join(' ')].join(' '))) add(w, m.featured ? 2 : 1);
  for (const w of Object.keys(SYNONYMS)) add(w, 3);
  prepared.vocab = [...words.entries()].sort((a, b) => b[1] - a[1]).map(([w]) => w);
  return prepared.vocab;
}

const same = (r, metric, operation, town) => r.kind === 'reading' && r.metric.key === metric && r.selection.domanda === operation && (r.selection.comune || null) === (town || null);

export function suggest(input, prepared, { previous = null, limit = 6 } = {}) {
  const raw = String(input || '');
  const text = normalize(raw);
  const out = [], seen = new Set();
  const push = (item, check) => {
    const key = normalize(item.text);
    if (seen.has(key) || out.length >= limit) return;
    const r = interpret(item.text, prepared, { previous: item.followUp ? previous : null });
    if (!check(r)) return;
    seen.add(key); out.push({ ...item, reading: r.selection?.domanda || null });
  };
  const prevReading = previous && previous.kind === 'reading' ? previous : null;
  // Seguiti della conversazione: utili a casella vuota o dopo «e…».
  if (prevReading && (!text || /^(e|ed|invece|anche)$/.test(text))) {
    const used = prevReading.selection.comune;
    for (const town of prepared.towns.filter(t => t.code !== used).slice(0, used ? 2 : 0))
      push({ text: `E a ${town.name}?`, followUp: true, kind: 'question' }, r => r.kind === 'reading' && r.selection.comune === town.code);
    for (const [op, q] of FOLLOW_UPS) if (prevReading.selection.domanda !== op)
      push({ text: q, followUp: true, kind: 'question' }, r => r.kind === 'reading' && r.selection.domanda === op && !r.notes.includes('requested_reading_unavailable'));
    return out;
  }
  if (text.length < 2) return out;
  const partial = /\s$/.test(raw) ? '' : (text.split(' ').at(-1) || '');
  // Comune già scritto, anche a metà («viar» → Viareggio).
  let towns = findTowns(text, prepared);
  if (!towns.length && partial.length >= 3) {
    const alias = Object.keys(TOWN_ALIASES).find(a => a.startsWith(partial));
    if (alias) towns = prepared.towns.filter(t => t.name === TOWN_ALIASES[alias]);
  }
  const words = tokens(stripQuestion(text));
  const complete = partial && words.at(-1) === partial ? words.slice(0, -1) : words;
  // Completamenti dell'ultima parola, poi indicatori più vicini.
  const completions = partial.length >= 3 && !towns.some(t => normalize(t.name).startsWith(partial))
    ? vocabulary(prepared).filter(w => w.startsWith(partial)).slice(0, 6) : [];
  const scores = new Map();
  for (const extra of completions.length ? completions : [null]) {
    for (const r of scoreMetrics(extra ? [...complete, extra] : complete, prepared).slice(0, 6))
      if (!scores.has(r.metric.key) || scores.get(r.metric.key).score < r.score) scores.set(r.metric.key, r);
  }
  const metrics = [...scores.values()].sort((a, b) => b.score - a.score).slice(0, 4).map(r => r.metric);
  // Incroci rivisti quando si parla di relazione o compaiono due indicatori.
  if (ASSOCIATION.test(text) || /\b(tra|fra)\b.*\be\b/.test(text)) {
    const keys = new Set(metrics.map(m => m.key));
    for (const a of prepared.associations || []) if (keys.has(a.left) || keys.has(a.right)) {
      const left = prepared.metrics.find(m => m.key === a.left), right = prepared.metrics.find(m => m.key === a.right);
      if (left && right) push({ text: `Relazione tra ${lower(left.label)} e ${lower(right.label)}`, kind: 'question', association: a.id }, r => r.kind === 'association' && r.association.id === a.id);
    }
  }
  const town = towns[0];
  // Senza Comune: invito a completarlo, senza inviare la domanda.
  const invite = metric => {
    const label = metric.label.charAt(0).toUpperCase() + metric.label.slice(1), key = normalize(label + ' a');
    if (town || !metric.operations.includes('observe') || out.length >= limit || seen.has(key)) return;
    seen.add(key); out.push({ text: label + ' a …', fill: label + ' a ', kind: 'complete', reading: 'observe' });
  };
  for (const metric of metrics) {
    const label = lower(metric.label);
    const order = town ? ORDER_TOWN : ORDER_ALL;
    if (metric === metrics[0]) invite(metric);
    let added = 0;
    for (const op of order) {
      if (added >= (metric === metrics[0] ? 3 : 1) || !metric.operations.includes(op)) continue;
      const q = TEMPLATES[op](label, town?.name);
      if (!q) continue;
      const before = out.length;
      push({ text: q.charAt(0).toUpperCase() + q.slice(1), kind: 'question' }, r => same(r, metric.key, op, town?.code));
      if (out.length > before) added++;
    }
  }
  return out;
}

// Testo della conferma: dice sempre che cosa è stato capito.
export const READINGS = { observe: 'il valore in un Comune', lookup: 'il dettaglio per località', compare: 'il confronto fra i sette Comuni', series: 'com’è cambiato nel tempo', rank: 'l’ordine dal valore più alto al più basso', benchmark_gap: 'il confronto con Toscana o Italia', absolute_change: 'quanto è cambiato (differenza)', relative_change: 'quanto è cambiato (in percentuale)', percentage_points: 'quanto è cambiato (in punti percentuali)', weighted_ratio: 'il valore della Versilia nel suo insieme', trend: 'la tendenza nel tempo', anomaly: 'i valori fuori scala fra i sette Comuni' };

// Frase di risposta costruita solo dall'evidenza del motore mostrata sotto.
// focus: Comuni nominati nella domanda («Viareggio contro Camaiore»), messi in primo piano.
export function summarize(evidence, townName, unitLabel, focus = []) {
  const step = evidence?.steps?.[0], request = evidence?.plan?.steps?.[0]?.request;
  const response = step?.response;
  if (!response || !request || response.status !== 'computed') return null;
  const fmt = (value, unit) => {
    if (typeof value !== 'number' || !Number.isFinite(value)) return null;
    const digits = Math.abs(value) >= 100 ? 0 : 2;
    const text = new Intl.NumberFormat('it-IT', { maximumFractionDigits: digits, useGrouping: 'always' }).format(value);
    const label = unitLabel(unit, request.selectors?.[0]?.metric);
    return label ? text + (['%', '€', '°C'].includes(label) ? (label === '€' ? ' €' : label) : ' ' + label) : text;
  };
  const period = p => (p === null || p === undefined) ? '' : ' (' + p + ')';
  const obs = (response.observations || []).filter(o => typeof o.value === 'number' && !o.dataUnavailable && !o.notApplicable);
  const r = response.result || {};
  switch (request.operation) {
    case 'observe': { const o = obs[0]; const v = o && fmt(o.value, o.unit); return v ? townName(o.geography) + ': ' + v + period(o.period) + '.' : null; }
    case 'rank': case 'compare': {
      if (obs.length < 2) return null;
      const named = focus.map(code => obs.find(o => o.geography === code)).filter(Boolean);
      if (named.length >= 2 && named.length === focus.length) {
        const order = [...named].sort((a, b) => b.value - a.value);
        const list = order.map(o => townName(o.geography) + ' ' + fmt(o.value, o.unit)).join(', ') + period(order[0].period) + '.';
        return list + (order[0].value === order[1].value ? ' Stesso valore.' : ' Valore più alto: ' + townName(order[0].geography) + '.') + ' Sotto, tutti e sette i Comuni.';
      }
      const sorted = [...obs].sort((a, b) => b.value - a.value), hi = sorted[0], lo = sorted[sorted.length - 1];
      if (hi.value === lo.value) return null;
      return 'Valore più alto: ' + townName(hi.geography) + ' con ' + fmt(hi.value, hi.unit) + '; più basso: ' + townName(lo.geography) + ' con ' + fmt(lo.value, lo.unit) + period(hi.period) + '. Un ordine numerico non è un giudizio.';
    }
    case 'series': {
      if (obs.length < 2) return null;
      const first = obs[0], last = obs[obs.length - 1];
      return townName(last.geography) + ': da ' + fmt(first.value, first.unit) + ' (' + first.period + ') a ' + fmt(last.value, last.unit) + ' (' + last.period + ').';
    }
    case 'absolute_change': case 'relative_change': case 'percentage_points': {
      const v = fmt(r.value, r.unit); if (!v) return null;
      return townName(request.selectors[0].towns[0]) + ': ' + (r.value > 0 ? '+' : '') + v + ' fra ' + r.startPeriod + ' e ' + r.endPeriod + '.';
    }
    case 'benchmark_gap': { const v = fmt(r.value, r.unit); return v ? townName(r.geography) + ' rispetto a ' + townName(r.benchmarkScope) + ': ' + (r.value > 0 ? '+' : '') + v + period(r.period) + '.' : null; }
    case 'weighted_ratio': { const v = fmt(r.value, r.unit); return v ? 'Versilia nel suo insieme: ' + v + period(r.period) + '.' : null; }
    default: return null;
  }
}

const NOTES = {
  requested_reading_unavailable: 'La lettura che chiedi non è disponibile per questo indicatore: mostro quella più vicina.',
  one_town_only: 'Questa lettura riguarda un Comune alla volta: uso il primo che hai nominato.',
};
const EXAMPLES = ['Quanti abitanti ha Viareggio?', 'Quale Comune ha il reddito più alto?', 'Com’è cambiata la popolazione di Massarosa negli anni?', 'Disoccupazione giovanile a Seravezza', 'C’è relazione tra reddito e popolazione?'];

// Interfaccia a messaggi sopra l'esploratore: ogni risposta è una selezione
// dell'esploratore esistente, che mostra numeri, fonti e limiti come sempre.
export function startAsk(index, presentation) {
  const prepared = prepare(index);
  const make = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
  const button = (text, onclick) => { const b = make('button', text, 'ask-chip'); b.type = 'button'; b.onclick = onclick; return b; };
  document.getElementById('ask-box')?.remove();
  const box = make('section', undefined, 'ask-box'); box.id = 'ask-box'; box.setAttribute('aria-labelledby', 'ask-title');
  const title = make('h3', 'Fai una domanda'); title.id = 'ask-title';
  const hint = make('p', 'Scrivi in italiano che cosa vuoi sapere sui sette Comuni. Ti dico come ho capito la domanda e ti mostro i dati verificati, con fonti e limiti. Le risposte vengono solo dal catalogo dell’Osservatorio.');
  const form = make('form'); form.id = 'ask-form'; form.setAttribute('role', 'search');
  const label = make('label', 'La tua domanda', 'ask-label'); label.htmlFor = 'ask-input';
  const input = make('input'); input.id = 'ask-input'; input.type = 'search'; input.maxLength = 200; input.autocomplete = 'off'; input.placeholder = 'Es.: reddito a Viareggio';
  // Suggeritore (schema combobox ARIA): proposte che si aggiornano mentre si scrive.
  const list = make('ul', undefined, 'ask-suggest'); list.id = 'ask-suggest'; list.setAttribute('role', 'listbox'); list.setAttribute('aria-label', 'Domande suggerite'); list.hidden = true;
  Object.entries({ role: 'combobox', 'aria-autocomplete': 'list', 'aria-expanded': 'false', 'aria-controls': 'ask-suggest' }).forEach(([k, v]) => input.setAttribute(k, v));
  const field = make('div', undefined, 'ask-field'); field.append(input, list);
  const send = make('button', 'Chiedi'); send.id = 'ask-send'; send.type = 'submit';
  form.append(label, field, send);
  const context = make('p', undefined, 'ask-context'); context.id = 'ask-context'; context.hidden = true;
  const examples = make('div', undefined, 'ask-examples'); examples.setAttribute('aria-label', 'Domande di esempio');
  for (const q of EXAMPLES) examples.append(button(q, () => { input.value = q; ask(q); }));
  const log = make('ol', undefined, 'ask-log'); log.id = 'ask-log'; log.setAttribute('aria-live', 'polite');
  box.append(title, hint, form, context, examples, log);
  const anchor = document.getElementById('association-modes') || document.getElementById('association-measure') || document.getElementById('explorer-form');
  anchor.before(box);

  const townName = code => index.towns.find(t => t.code === code)?.name || code;
  const metricLabel = key => index.metrics.find(m => m.key === key)?.label || key;
  function say(question) {
    const item = make('li', undefined, 'ask-turn');
    item.append(make('p', question, 'ask-question'));
    const answer = make('div', undefined, 'ask-answer'); item.append(answer);
    log.prepend(item);
    while (log.children.length > 6) log.lastChild.remove();
    return answer;
  }
  function measureMode() { document.getElementById('association-mode-measure')?.click(); }
  // Il nome proprio della misura (abitanti, posti letto…) prevale sull'unità generica.
  const unitLabel = (unit, metric) => { const m = presentation?.metrics?.[metric]; return m?.unit === unit && typeof m.unitLabel === 'string' ? m.unitLabel : (units[unit] ?? ''); };
  const townLabel = code => ({ tuscany: 'Toscana', italy: 'Italia' })[code] || townName(code);
  let waiting = null;
  // Quando l'esploratore mostra il risultato, la risposta riceve la frase e la pagina scorre fino ai dati.
  const result = document.getElementById('explorer-result'), consent = document.getElementById('explorer-consent');
  new MutationObserver(() => {
    if (!waiting) return;
    const pre = result.querySelector('[data-explorer-evidence]');
    let evidence = null; try { evidence = pre && JSON.parse(pre.textContent); } catch {}
    const req = evidence?.plan?.steps?.[0]?.request, sel = waiting.selection;
    const matches = req && req.operation === sel.domanda && req.selectors?.[0]?.metric === sel.indicatore && req.selectors[0].dimension === sel.dettaglio
      && (!sel.comune || req.selectors[0].towns?.includes(sel.comune));
    if (!result.hidden && matches) {
      const { answer: target, focus } = waiting; waiting = null;
      const sentence = summarize(evidence, townLabel, unitLabel, focus);
      if (sentence) target.append(make('p', sentence, 'ask-reply'));
      target.append(make('p', 'Dati, fonti e limiti qui sotto.', 'ask-note'));
      sourceLink(index.metrics.find(m => m.key === sel.indicatore), target);
      result.scrollIntoView({ block: 'start' });
    } else if (!consent.hidden) {
      const target = waiting.answer; waiting = null;
      target.append(make('p', 'Per almeno un Comune il dato manca: conferma qui sotto per vedere gli altri con i limiti indicati.', 'ask-note'));
      sourceLink(index.metrics.find(m => m.key === sel.indicatore), target);
      consent.scrollIntoView({ block: 'center' });
    }
  }).observe(document.getElementById('a7-explorer'), { subtree: true, childList: true, attributes: true, attributeFilter: ['hidden'] });
  function apply(selection, answer, focus = []) {
    measureMode(); waiting = answer ? { answer, selection, focus } : null;
    const params = new URLSearchParams();
    for (const key of ['indicatore', 'dettaglio', 'domanda', 'comune', 'riferimento']) if (selection[key]) params.set(key, selection[key]);
    const hash = '#esplora&' + params.toString();
    if (location.hash === hash) location.hash = '';
    location.hash = hash;
  }
  // Incrocio rivisto: stessa logica, la frase riporta il coefficiente del motore.
  function pair(id, answer) {
    const out = document.getElementById('association-result');
    document.getElementById('association-mode-pair')?.click();
    if (out) {
      const watch = new MutationObserver(() => {
        const pre = out.querySelector('[data-association-evidence]');
        if (out.hidden || !pre) return;
        let evidence = null; try { evidence = JSON.parse(pre.textContent); } catch {}
        if (evidence?.plan?.steps?.[0]?.id !== id) return;
        watch.disconnect();
        const r = evidence.steps[0].response;
        if (r.status === 'computed') answer.append(make('p', 'Coefficiente di Spearman ' + new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(r.result.coefficient) + ' su ' + r.result.n + ' Comuni (scala da −1 a +1). Descrive se gli ordini dei Comuni coincidono, non una causa.', 'ask-reply'));
        answer.append(make('p', 'Grafico, coppie, fonti e limiti qui sotto.', 'ask-note'));
        const a = index.associations.find(x => x.id === id);
        for (const key of a ? [a.left, a.right] : []) sourceLink(index.metrics.find(m => m.key === key), answer);
        out.scrollIntoView({ block: 'start' });
      });
      watch.observe(out, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
    }
    document.dispatchEvent(new CustomEvent('chiedi-association', { detail: { id } }));
  }
  // Conversazione: l'ultima lettura riuscita permette domande come «e a Camaiore?».
  let current = null;
  function remember(r) {
    current = r;
    context.replaceChildren();
    if (!r) { context.hidden = true; return; }
    const parts = [r.metric.label]; if (r.viewLabel) parts.push(r.viewLabel); if (r.selection.comune) parts.push(townName(r.selection.comune));
    const other = index.towns.find(t => t.code !== r.selection.comune && t.name.length < 10)?.name || 'Camaiore';
    context.append(make('span', 'Stai parlando di: ' + parts.join(' · ') + '. Puoi continuare, per esempio: «e a ' + other + '?», «e nel tempo?». '));
    const reset = make('button', 'Nuovo argomento', 'ask-reset'); reset.type = 'button'; reset.onclick = () => { remember(null); input.focus(); };
    context.append(reset); context.hidden = false;
  }
  function sourceLink(metric, answer) {
    if (!metric?.page) return;
    const line = make('p', undefined, 'ask-source'); const a = make('a', 'Fonte e metodo: «' + metric.label + '» sull’Osservatorio');
    a.href = metric.page; a.target = '_blank'; a.rel = 'noopener';
    line.append(a); answer.append(line);
  }
  function describe(r) {
    const parts = ['«' + (r.viewLabel && r.metric.short ? r.metric.short : r.metric.label) + '»'];
    if (r.viewLabel) parts.push(r.viewLabel);
    parts.push(READINGS[r.selection.domanda] || r.selection.domanda);
    if (r.selection.comune) parts.push(townName(r.selection.comune));
    else if (r.towns?.length >= 2 && ['rank', 'compare'].includes(r.selection.domanda)) parts.push('in evidenza ' + r.towns.map(t => t.name).join(' e '));
    if (r.selection.riferimento) parts.push(r.selection.riferimento === 'italy' ? 'rispetto all’Italia' : 'rispetto alla Toscana');
    return (r.followUp ? 'Continuo dalla domanda precedente. ' : '') + 'Ho capito: ' + parts.join(' · ') + '.';
  }
  function ask(question, options = {}, reuse = null) {
    const r = interpret(question, prepared, { previous: current, ...options });
    const answer = reuse || say(question);
    answer.replaceChildren();
    if (r.kind === 'empty') { answer.append(make('p', 'Scrivi una domanda, per esempio sul reddito o sulla popolazione di un Comune.')); return; }
    if (r.kind === 'no_metric' && r.towns.length >= 2) {
      // «Viareggio contro Camaiore»: i Comuni ci sono, manca su che cosa confrontarli.
      const names = r.towns.map(t => t.name).join(' e ');
      answer.append(make('p', 'Su quale indicatore vuoi confrontare ' + names + '?'));
      const list = make('div', undefined, 'ask-options');
      const common = ['population', 'income', 'unemploymentRate', 'oldAgeIndex', 'tourismPresences', 'recycling', 'omiResidential', 'foreignResidents'];
      for (const m of common.map(k => index.metrics.find(m => m.key === k)).filter(m => m?.operations.includes('rank')))
        list.append(button(m.label, () => ask(m.label + ': ' + names, {}, answer)));
      answer.append(list); return;
    }
    if (r.kind === 'no_metric') {
      answer.append(make('p', 'Non ho trovato un indicatore che risponda a questa domanda nel catalogo. Prova con altre parole (per esempio reddito, turismo, rifiuti, scuola) oppure scegli un tema qui sotto.'));
      return;
    }
    if (r.kind === 'association') {
      const a = r.association;
      answer.append(make('p', 'Ho capito: la relazione fra «' + metricLabel(a.left) + '» e «' + metricLabel(a.right) + '» nei sette Comuni. È una lettura descrittiva: non dimostra una causa.'));
      pair(a.id, answer);
      return;
    }
    if (r.kind === 'association_unavailable') {
      answer.append(make('p', 'Questo incrocio non è ancora stato rivisto, quindi non lo mostro. Gli incroci disponibili sono:'));
      const list = make('div', undefined, 'ask-options');
      for (const a of index.associations) list.append(button(metricLabel(a.left) + ' e ' + metricLabel(a.right), () => pair(a.id, answer)));
      answer.append(list); return;
    }
    if (r.kind === 'no_reading') { answer.append(make('p', 'Ho trovato «' + r.metric.label + '», ma per questo indicatore non ci sono ancora letture consultabili qui.')); return; }
    const notes = r.notes.filter(n => NOTES[n]).map(n => NOTES[n]);
    if (r.notes.includes('town_needed')) {
      answer.append(make('p', describe(r).replace(/\.$/, '') + ' — in quale Comune?'));
      const towns = make('div', undefined, 'ask-options');
      for (const t of [...index.towns].sort((a, b) => a.name.localeCompare(b.name, 'it'))) towns.append(button(t.name, () => { const s = { ...r.selection, comune: t.code }; answer.querySelector('p').textContent = describe({ ...r, selection: s }); towns.remove(); remember({ ...r, selection: s }); apply(s, answer); }));
      answer.append(towns);
      remember(r);
    } else {
      answer.append(make('p', describe(r)));
      remember(r);
      const both = ['rank', 'compare'].includes(r.selection.domanda) && r.towns.length >= 2 ? r.towns.map(t => t.code) : [];
      apply(r.selection, answer, both);
    }
    for (const note of notes) answer.append(make('p', note, 'ask-note'));
    if (r.alternatives.length) {
      const other = make('div', undefined, 'ask-options'); other.append(make('span', 'Intendevi un altro indicatore? '));
      for (const m of r.alternatives) other.append(button(m.label, () => ask(question, { metric: m.key }, answer)));
      answer.append(other);
    }
  }
  let options = [], active = -1, timer = null;
  const close = () => { list.hidden = true; list.replaceChildren(); options = []; active = -1; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); };
  function choose(item) {
    if (item.kind === 'complete') { input.value = item.fill; input.focus(); refresh(); return; }
    input.value = ''; close(); ask(item.text);
  }
  function highlight(i) {
    active = i;
    [...list.children].forEach((li, j) => li.setAttribute('aria-selected', String(j === i)));
    if (i >= 0) input.setAttribute('aria-activedescendant', list.children[i].id); else input.removeAttribute('aria-activedescendant');
  }
  function refresh() {
    options = suggest(input.value, prepared, { previous: current });
    list.replaceChildren(); active = -1; input.removeAttribute('aria-activedescendant');
    options.forEach((item, i) => {
      const li = make('li', undefined, 'ask-suggestion'); li.id = 'ask-suggest-' + i; li.setAttribute('role', 'option'); li.setAttribute('aria-selected', 'false');
      li.append(make('span', item.text, 'ask-suggestion-text'));
      if (item.reading) li.append(make('span', item.kind === 'complete' ? 'scegli il Comune' : (READINGS[item.reading] || ''), 'ask-suggestion-kind'));
      // pointerdown: la scelta avviene prima che il campo perda il fuoco.
      li.addEventListener('pointerdown', event => { event.preventDefault(); choose(item); });
      list.append(li);
    });
    const open = options.length > 0 && document.activeElement === input;
    list.hidden = !open; input.setAttribute('aria-expanded', String(open));
  }
  input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(refresh, 90); });
  input.addEventListener('focus', refresh);
  input.addEventListener('blur', () => setTimeout(close, 120));
  input.addEventListener('keydown', event => {
    if (event.key === 'ArrowDown' && options.length) { event.preventDefault(); if (list.hidden) refresh(); highlight((active + 1) % options.length); }
    else if (event.key === 'ArrowUp' && options.length) { event.preventDefault(); highlight(active <= 0 ? options.length - 1 : active - 1); }
    else if (event.key === 'Escape' && !list.hidden) { event.preventDefault(); close(); }
    else if (event.key === 'Enter' && active >= 0 && !list.hidden) { event.preventDefault(); choose(options[active]); }
  });
  form.onsubmit = event => { event.preventDefault(); close(); const q = input.value.trim(); if (q) { input.value = ''; ask(q); } };
  // Domanda arrivata da un'altra pagina (mascotte Versilia): ?q=… viene posta subito e tolta dall'indirizzo.
  const incoming = new URLSearchParams(location.search).get('q')?.trim().slice(0, 200);
  if (incoming) {
    try { const url = new URL(location.href); url.searchParams.delete('q'); history.replaceState(null, '', url.pathname + url.search + url.hash); } catch {}
    box.scrollIntoView({ block: 'start' });
    ask(incoming);
  }
  return { ask };
}
