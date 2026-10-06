#!/usr/bin/env python3
"""Fetch recent awards from the Plataforma de Contratacion del Sector Publico (Atom feeds),
keep culture/archives/documentation-related ones, write data/es.json. Real data only."""
import json, os, re, sys, time, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

FEEDS = [
 'https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_1044/PlataformasAgregadasSinMenores.atom',
 'https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom',
]
BACKFILL_DAYS = int(os.environ.get('BACKFILL_DAYS', '60'))
KEEP_DAYS = 400
MAX_PAGES = int(os.environ.get('MAX_PAGES', '600'))
OUT = Path('data'); OUT.mkdir(parents=True, exist_ok=True)
CPV = ['79131','72512','79995','92512','72268','79999','72314','92511','92521','92522','92520','92510','92500','48311','48312','72310','72320','72322']
KW = ['ARXIU','ARCHIV','GESTIÓ DOCUMENTAL','GESTIÓN DOCUMENTAL','DIGITALITZ','DIGITALIZ','ESCANEIG','ESCANEO','CATALOGACI','GESTIÓ BIBLIOTEC','GESTIÓN BIBLIOTEC','BIBLIOTEC','PATRIMONI CULTURAL','PATRIMONIO CULTURAL','PATRIMONI DOCUMENTAL','PATRIMONIO DOCUMENTAL','INVENTARI DE','INVENTARIO DE','PRESERVACI','CONSERVACI DIGITAL','CONSERVACIÓN DIGITAL','REPOSITORI','METADAD','DIGITAL HERITAGE','MUSEO','MUSEU','FONDO DOCUMENTAL','FONS DOCUMENTAL','HEMEROTECA']
NS = {'a':'http://www.w3.org/2005/Atom','cbc':'urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2','cac':'urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2','pe':'urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2','pb':'urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2'}
TYPES = {'1':'Suministros','2':'Servicios','3':'Obras','21':'Servicios','22':'Servicios','7':'Administrativo especial','8':'Privado','40':'Colaboración','31':'Concesión de obras','32':'Concesión de servicios','50':'Patrimonial'}

def get(url):
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Adjudicaciones tracker)'})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:
            print('retry', url, e, file=sys.stderr); time.sleep(3)
    raise RuntimeError('fetch failed '+url)

def t(el, path):
    x = el.find(path, NS)
    return (x.text or '').strip() if x is not None and x.text else ''

def relevant(cpvs, text):
    up = text.upper()
    return any(c.startswith(p) for c in cpvs for p in CPV) or any(w in up for w in KW)

def parse(root, cutoff_dt):
    rows = []; oldest = None
    for e in root.findall('a:entry', NS):
        upd = t(e, 'a:updated')
        try: d = datetime.fromisoformat(upd)
        except Exception: d = None
        if d and (oldest is None or d < oldest): oldest = d
        cf = e.find('pe:ContractFolderStatus', NS)
        if cf is None: continue
        title = t(e, 'a:title'); eid = t(e, 'a:id')
        link = e.find('a:link', NS); url = link.get('href') if link is not None else ''
        organ = t(cf, 'pe:LocatedContractingParty/cac:Party/cac:PartyName/cbc:Name')
        proj = cf.find('cac:ProcurementProject', NS)
        cpvs = [x.text.strip() for x in proj.findall('cac:RequiredCommodityClassification/cbc:ItemClassificationCode', NS) if x.text] if proj is not None else []
        for lot in (proj.findall('cac:ProcurementProjectLot', NS) if proj is not None else []):
            cpvs += [x.text.strip() for x in lot.findall('cac:ProcurementProject/cac:RequiredCommodityClassification/cbc:ItemClassificationCode', NS) if x.text]
        typ = t(proj, 'cbc:TypeCode') if proj is not None else ''
        exp = t(cf, 'cbc:ContractFolderID')
        for tr in cf.findall('cac:TenderResult', NS):
            code = t(tr, 'cbc:ResultCode')
            if code not in ('8', '9'): continue   # solo adjudicado / formalizado
            win = tr.find('cac:WinningParty', NS)
            if win is None: continue
            name = t(win, 'cac:PartyName/cbc:Name'); nif = t(win, 'cac:PartyIdentification/cbc:ID')
            if not name: continue
            amt = t(tr, 'cac:AwardedTenderedProject/cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount')
            date = t(tr, 'cbc:AwardDate') or t(tr, 'cac:Contract/cbc:IssueDate') or upd[:10]
            if not relevant(cpvs, title): continue
            rows.append({'id': eid + '#' + (nif or name), 'data_publicacio_adjudicacio': date, 'nom_organ': organ, 'denominacio': title,
                'codi_cpv': '||'.join(dict.fromkeys(cpvs)), 'denominacio_adjudicatari': name, 'identificacio_adjudicatari': nif,
                'import_adjudicacio_sense': (amt if amt and float(amt) > 0 else None), 'enllac_publicacio': {'url': url}, 'codi_expedient': exp,
                'tipus_contracte': TYPES.get(typ, ''), 'estat': 'Formalizado' if code == '9' else 'Adjudicado', 'updated': upd, 'font': 'ES'})
    return rows, oldest

def main():
    now = datetime.now(timezone.utc)
    prev = {}
    p = OUT / 'es.json'
    last = None
    if p.exists():
        try:
            old = json.loads(p.read_text(encoding='utf-8'))
            for r in old.get('rows', []): prev[r['id']] = r
            last = datetime.fromisoformat(old['fetchedAt'])
        except Exception as ex: print('prev unreadable', ex, file=sys.stderr)
    state = old.get('state', {}) if last else {}
    deadline = time.time() + int(os.environ.get('BUDGET_MIN', '40')) * 60
    head_cut = (last - timedelta(days=2)) if last else now - timedelta(days=2)
    back_cut = now - timedelta(days=BACKFILL_DAYS)
    stats = {}
    def walk(url, cut):
        """returns pages, rows, next unvisited url (None if finished), reached cut"""
        pages = 0; got = 0
        while url and time.time() < deadline:
            root = ET.fromstring(get(url)); pages += 1
            rows, oldest = parse(root, cut)
            for r in rows:
                if r['id'] not in prev or r['updated'] >= prev[r['id']]['updated']: prev[r['id']] = r
            got += len(rows)
            nxt = next((l.get('href') for l in root.findall('a:link', NS) if l.get('rel') == 'next'), None)
            nxt = nxt.replace('contrataciondelestado.es', 'contrataciondelsectorpublico.gob.es') if nxt else None
            if oldest is None or oldest < cut: return pages, got, nxt, True
            url = nxt
        return pages, got, url, False
    ok = True
    for feed in FEEDS:
        st = state.setdefault(feed, {})
        try:
            pa, ga, nxt, hit = walk(feed, head_cut)
            stats[feed] = {'head_pages': pa, 'head_rows': ga, 'head_complete': hit}
            if not hit: ok = False
            if hit and 'resume' not in st and not st.get('done'): st['resume'] = nxt
            if st.get('resume') and not st.get('done'):
                pb, gb, nxt2, hit2 = walk(st['resume'], back_cut)
                stats[feed].update({'back_pages': pb, 'back_rows': gb})
                if hit2 or nxt2 is None: st['done'] = True; st['resume'] = None
                else: st['resume'] = nxt2
            stats[feed]['backfill_done'] = bool(st.get('done'))
        except Exception as ex:
            ok = False; stats[feed] = {'error': str(ex)}; print('feed failed', feed, ex, file=sys.stderr)
    keep_from = (now - timedelta(days=KEEP_DAYS)).strftime('%Y-%m-%d')
    seen = {}
    for r in prev.values():
        k = (r['codi_expedient'], r['identificacio_adjudicatari'], r['import_adjudicacio_sense'])
        if k not in seen or r['updated'] > seen[k]['updated']: seen[k] = r
    prev = {r['id']: r for r in seen.values()}
    rows = sorted((r for r in prev.values() if r['data_publicacio_adjudicacio'] >= keep_from), key=lambda r: r['data_publicacio_adjudicacio'], reverse=True)
    if not rows and not prev: sys.exit('no data, not overwriting')
    out = {'fetchedAt': (now.isoformat() if ok else (last.isoformat() if last else now.isoformat())), 'checkedAt': now.isoformat(), 'stats': stats, 'state': state, 'rows': rows}
    p.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'rows': len(rows), 'stats': stats}))
main()
