# --- Robust contest name normalization ---
def normalize_party(party):
    p = (party or '').strip().upper()
    if p in ('REP', 'REPUBLICAN', 'R', 'GOP'):
        return 'REP'
    if p in ('DEM', 'DEMOCRAT', 'D', 'DFL'):
        return 'DEM'
    return p or 'OTHER'
import string
def normalize_contest_name(name):
    if not name:
        return ''
    # Remove punctuation, collapse whitespace, uppercase
    name = name.strip().upper()
    name = ''.join(ch if ch not in string.punctuation else ' ' for ch in name)
    name = ' '.join(name.split())
    return name

def extract_all_contest_names(input_glob, output_txt):
    files = glob.glob(input_glob)
    files = sorted(files)
    names_by_year_file = {}
    for fp in files:
        # Extract year from filename if possible
        m = re.search(r'(20\d{2})', fp)
        year = m.group(1) if m else 'unknown'
        if year not in names_by_year_file:
            names_by_year_file[year] = {}
        fname = os.path.basename(fp)
        if fname not in names_by_year_file[year]:
            names_by_year_file[year][fname] = set()
        print('Scanning', fp)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    name = row.get('Contest Name') or row.get('Contest')
                    if name:
                        names_by_year_file[year][fname].add(name.strip())
        except Exception as e:
            print('Error reading', fp, e)
    with open(output_txt, 'w', encoding='utf-8') as outf:
        for year in sorted(names_by_year_file.keys()):
            outf.write(f'==== {year} ====' + '\n')
            for fname in sorted(names_by_year_file[year].keys()):
                outf.write(f'  -- {fname} --' + '\n')
                for name in sorted(names_by_year_file[year][fname]):
                    outf.write('    ' + name + '\n')
                outf.write('\n')
            outf.write('\n')
    total_names = sum(len(names) for year in names_by_year_file.values() for names in year.values())
    print(f'Wrote {total_names} unique contest names (grouped by year and file) to', output_txt)
#!/usr/bin/env python3
import csv
import glob
import json
import os
import re
import argparse
from collections import defaultdict, Counter

# Mapping for competitiveness thresholds and colors (from metadata)
COMP_MAP = [
    (40, 'Annihilation', '#67000d', 'R_ANNIHILATION'),
    (30, 'Dominant', '#a50f15', 'R_DOMINANT'),
    (20, 'Stronghold', '#cb181d', 'R_STRONGHOLD'),
    (10, 'Safe', '#ef3b2c', 'R_SAFE'),
    (5.5, 'Likely', '#fb6a4a', 'R_LIKELY'),
    (1, 'Lean', '#fcae91', 'R_LEAN'),
    (0.5, 'Tilt', '#fee8c8', 'R_TILT')
]
DEM_COMP_MAP = [
    (40, 'Annihilation', '#08306b', 'D_ANNIHILATION'),
    (30, 'Dominant', '#08519c', 'D_DOMINANT'),
    (20, 'Stronghold', '#3182bd', 'D_STRONGHOLD'),
    (10, 'Safe', '#6baed6', 'D_SAFE'),
    (5.5, 'Likely', '#9ecae1', 'D_LIKELY'),
    (1, 'Lean', '#c6dbef', 'D_LEAN'),
    (0.5, 'Tilt', '#e1f5fe', 'D_TILT')
]

# Contests of interest keywords
PRESIDENT_KEYS = ['PRESIDENT']
US_SENATE_KEYS = ['US SENATE', 'UNITED STATES SENATE']
JUDICIAL_KEYS = ['SUPREME COURT', 'COURT OF APPEALS']
COUNCIL_KEYS = [
    'GOVERNOR', 'LIEUTENANT GOVERNOR', 'SECRETARY OF STATE', 'STATE AUDITOR',
    'STATE TREASURER', 'SUPERINTENDENT OF PUBLIC INSTRUCTION', 'ATTORNEY GENERAL',
    'COMMISSIONER OF AGRICULTURE', 'COMMISSIONER OF LABOR', 'COMMISSIONER OF INSURANCE'
]

# Try to build exact-match inclusion sets from data/all_contest_names.txt if it exists.
ALL_NAMES_PATH = 'data/all_contest_names.txt'
PRESIDENT_SET = set()
US_SENATE_SET = set()
JUDICIAL_SET = set()
COUNCIL_SET = set()

def _load_inclusion_sets():
    if not os.path.exists(ALL_NAMES_PATH):
        return
    try:
        with open(ALL_NAMES_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                # Aggressive reflow: fix hard-wrapped ALL-CAPS contest names
                line = re.sub(r'([A-Z])\r?\n\s+([A-Z])', r'\1 \2', line)
                n = normalize_contest_name(line)
                if not n:
                    continue
                # President
                if any(kw in n for kw in PRESIDENT_KEYS):
                    PRESIDENT_SET.add(n)
                # US Senate
                if 'SENATE' in n and (any(kw in n for kw in ['US', 'U S', 'UNITED STATES'])):
                    US_SENATE_SET.add(n)
                # Judicial
                if any(kw in n for kw in JUDICIAL_KEYS):
                    JUDICIAL_SET.add(n)
                # Council of State
                for kw in COUNCIL_KEYS:
                    if kw in n:
                        COUNCIL_SET.add(n)
    except Exception:
        pass

# populate at import time
_load_inclusion_sets()

def slugify(name):
    s = re.sub(r"[^A-Za-z0-9]+", "_", name.strip())
    s = re.sub(r"_+", "_", s)
    return s.strip('_').lower()

def classify_margin(margin_pct):
    if margin_pct is None:
        return {'category':'Unknown','party':None,'code':None,'color':None}
    if abs(margin_pct) <= 0.5:
        return {'category':'Tossup','party':'Tossup','code':'TOSSUP','color':'#f7f7f7'}
    if margin_pct > 0:
        # Republican advantage
        for threshold, cat, color, code in COMP_MAP:
            if margin_pct >= threshold:
                return {'category':cat, 'party':'Republican','code':code,'color':color}
        return {'category':'Tilt','party':'Republican','code':'R_TILT','color':'#fee8c8'}
    else:
        # Democratic advantage
        am = abs(margin_pct)
        for threshold, cat, color, code in DEM_COMP_MAP:
            if am >= threshold:
                return {'category':cat, 'party':'Democratic','code':code,'color':color}
        return {'category':'Tilt','party':'Democratic','code':'D_TILT','color':'#e1f5fe'}


def row_total_votes(row):
    # prefer 'Total Votes' field but try alternatives
    for k in ['Total Votes','Total','Total Votes ', 'TotalVotes']:
        if k in row and row[k].strip()!='':
            try:
                return int(float(row[k]))
            except:
                pass
    # fallback sum of known columns (check both lowercase and capitalized)
    total = 0
    vote_columns = ['election day','one stop','absentee by mail','provisional',
                   'Election Day','One Stop','Absentee by Mail','Provisional']
    for k in vote_columns:
        if k in row and row[k].strip()!='':
            try:
                total += int(float(row[k]))
            except:
                pass
    return total


def is_desired_contest(contest_name):
    n = normalize_contest_name(contest_name)
    # exact-match inclusion check (higher priority)
    if n in PRESIDENT_SET:
        return 'presidential'
    if n in US_SENATE_SET:
        return 'us_senate'
    if n in JUDICIAL_SET:
        return 'judicial'
    if n in COUNCIL_SET:
        return 'council_of_state'
    # President: any contest containing 'PRESIDENT' (allow 'PRESIDENT AND VICE PRESIDENT' phrasing)
    if 'PRESIDENT' in n:
        return 'presidential'
    # US Senate: match when the contest explicitly references US / U S / UNITED STATES (avoid matching STATE SENATE)
    if 'SENATE' in n and (" US " in f" {n} " or 'U S' in n or 'UNITED STATES' in n):
        return 'us_senate'
    # Judicial: any contest containing 'SUPREME COURT' or 'COURT OF APPEALS'
    if 'SUPREME COURT' in n or 'COURT OF APPEALS' in n:
        return 'judicial'
    # Council of State: match a set of office keywords anywhere in the contest name
    council_keywords = [
        'GOVERNOR',
        'LIEUTENANT GOVERNOR',
        'SECRETARY OF STATE',
        'AUDITOR',
        'TREASURER',
        'SUPERINTENDENT',
        'ATTORNEY GENERAL',
        'COMMISSIONER OF AGRICULTURE',
        'COMMISSIONER OF LABOR',
        'COMMISSIONER OF INSURANCE'
    ]
    for kw in council_keywords:
        if kw in n:
            return 'council_of_state'
    return None


def aggregate_csv_files(input_glob, output_path, existing_path=None):
    files = glob.glob(input_glob)
    # For 2012, only use the one intended clean file to avoid double-counting
    filtered_files = []
    for fp in files:
        basename = os.path.basename(fp)
        m = re.search(r'(20\d{2})', fp)
        year = m.group(1) if m else 'unknown'
        if year == '2012':
            # Only use results_pct_20121106_clean.csv for 2012
            if basename == 'results_pct_20121106_clean.csv':
                filtered_files.append(fp)
            else:
                print(f"[SKIP] Ignoring extra 2012 file: {basename}")
        else:
            filtered_files.append(fp)
    data = defaultdict(lambda: defaultdict(dict))
    for fp in filtered_files:
        basename = os.path.basename(fp)
        m = re.search(r'(20\d{2})', fp)
        year = m.group(1) if m else 'unknown'
        print(f'Processing {fp} (year: {year})')
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            # Normalize header names
            reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
            contest_fields = ['contest name', 'contest', 'contest_name']
            contest_col = None
            for h in reader.fieldnames:
                if h and h.strip().lower() in contest_fields:
                    contest_col = h
                    break
            if not contest_col:
                # Try normalized header match first
                for h in (reader.fieldnames or []):
                    if h and h.strip().lower().replace(' ','') in [x.replace(' ','') for x in contest_fields]:
                        contest_col = h
                        break
            debug_names = set()
            found_any = False
            unmatched_contests = set()
            for i, row in enumerate(reader):
                # Normalize row keys and values, strip whitespace from keys and values
                row = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                contest = (row.get(contest_col) or '').strip() if contest_col else ''
                contest_norm = normalize_contest_name(contest)
                if i < 5 and contest:
                    debug_names.add(contest)
                if not contest:
                    continue
                # Only include targeted contests
                group = is_desired_contest(contest)
                # Exclude judicial races before 2018
                if group == 'judicial' and int(year) < 2018:
                    continue
                if not group:
                    unmatched_contests.add(contest)
                    continue
                found_any = True
                county = row.get('county','').strip().upper()
                if not county:
                    continue
                candidate_name = row.get('choice','').strip()
                # Normalize suffix commas like " , Jr." or ", Jr" -> " Jr." so splitting works
                try:
                    candidate_name = re.sub(r"\s*,\s*(Jr\.?|Sr\.?)\b", r" \1", candidate_name, flags=re.IGNORECASE)
                except Exception:
                    pass
                candidate_name = re.sub(r"\s+", ' ', candidate_name).strip()
                # remove any stray trailing commas
                if candidate_name.endswith(','):
                    candidate_name = candidate_name[:-1].strip()
                # If candidate_name contains a comma and party is missing, try to split
                party_raw = (row.get('party','') or row.get('choice party','') or '')
                # If the CSV has a bad 'party' value (e.g. 'Jr.'), fold it back into the candidate
                # name unless it maps to a known party code after normalization.
                known_parties = {'REP','DEM','LIB','GRE','CST','UNA','CON','IND','NPA','WCP','LBT','GOP'}
                if party_raw:
                    try:
                        pr_norm = normalize_party(party_raw)
                    except Exception:
                        pr_norm = (party_raw or '').strip().upper()
                    if pr_norm not in known_parties:
                        # append the stray party-like value back onto the candidate name
                        if party_raw not in candidate_name:
                            candidate_name = (candidate_name + ', ' + party_raw).strip() if candidate_name else party_raw
                        party_raw = ''
                        # After folding back the stray value, check again if the candidate_name
                        # now ends with a known party token (e.g. ", REP") and extract it.
                        try:
                            if ',' in candidate_name:
                                parts_after = [p.strip() for p in candidate_name.split(',') if p.strip()]
                                if len(parts_after) > 1 and normalize_party(parts_after[-1]) in known_parties:
                                    party_raw = parts_after[-1]
                                    candidate_name = ', '.join(parts_after[:-1])
                        except Exception:
                            pass
                if not party_raw and ',' in candidate_name:
                        # Normalize suffix commas like " , Jr." or ", Jr" -> " Jr." so splitting works
                        try:
                            candidate_name = re.sub(r"\s*,\s*(Jr\.?|Sr\.?)\b", r" \1", candidate_name, flags=re.IGNORECASE)
                        except Exception:
                            pass
                        candidate_name = re.sub(r"\s+", ' ', candidate_name).strip()
                        # remove any stray trailing commas
                        if candidate_name.endswith(','):
                            candidate_name = candidate_name[:-1].strip()
                        parts = [p.strip() for p in candidate_name.split(',') if p.strip()]
                        known_parties = {'REP','DEM','LIB','GRE','CST','UNA','CON','IND','NPA','WCP','LBT','GOP'}
                        if len(parts) > 1 and normalize_party(parts[-1]) in known_parties:
                            party_raw = parts[-1]
                            candidate_name = ', '.join(parts[:-1])
                        else:
                            candidate_name = ', '.join(parts)
                            party_raw = ''
                # If the party was split into the wrong CSV column (e.g. an unquoted comma
                # caused "Phil Berger , Jr. , REP" to become Choice="Phil Berger",
                # Choice Party="Jr.", and the real 'REP' landed in the next column),
                # try to find a known party token anywhere in the row and use that.
                if not party_raw:
                    for col in (reader.fieldnames or []):
                        try:
                            val = (row.get(col) or '').strip()
                        except Exception:
                            val = ''
                        if val and normalize_party(val) in known_parties:
                            party_raw = val
                            # clear the source cell so votes don't get mis-attributed later
                            row[col] = ''
                            break

                party = normalize_party(party_raw)
                    # Special-case: Christopher Anglin ran as REP in 2018 Supreme Court but was a Democrat
                # Robust special-case: Christopher (Chris) Anglin ran as REP in 2018 Supreme Court; move him to OTHER, not DEM or REP
                if (
                    year == '2018'
                    and group == 'judicial'
                    and 'SUPREME COURT' in contest.upper()
                ):
                    name_lc = candidate_name.lower().replace('(', '').replace(')', '').replace('.', '').replace('  ', ' ')
                    if 'anglin' in name_lc:
                        party = 'OTHER'
                
                # Targeted debug print for every row of 2020 Supreme Court Associate Justice Seat 02
                if year == '2020' and 'SUPREME COURT ASSOCIATE JUSTICE SEAT 02' in contest.upper() and 'berger' in (row.get('choice','').lower()):
                    print(f"[ROW DEBUG] {county}: candidate_raw='{row.get('choice','')}' party_raw='{party_raw}' party='{party}' votes='{row.get('total votes','0')}' KEYS={list(row.keys())} FULL_ROW={row}")
                # Debug print for 2020 Supreme Court Seat 02
                if year == '2020' and 'SUPREME COURT ASSOCIATE JUSTICE SEAT 02' in contest.upper():
                    print(f"[DEBUG] {county}: candidate='{candidate_name}' party_raw='{party_raw}' party='{party}' votes={row.get('total votes','0')}")
                # Compute votes for this row.
                # Default behavior: prefer an explicit 'total votes' cell when present
                # because summing partial columns can sometimes double-count or miss
                # split columns. However, the 2020 "SUPREME COURT ASSOCIATE JUSTICE
                # SEAT 02" contest had malformed 'Total Votes' values in the source
                # files (they were unreliable), so for that specific contest we
                # deliberately sum the underlying vote columns instead. This
                # special-case is limited to that contest to avoid inflating other
                # contests.
                use_sum = False
                try:
                    if year == '2020' and 'SUPREME COURT ASSOCIATE JUSTICE SEAT 02' in contest.upper():
                        use_sum = True
                except Exception:
                    use_sum = False

                if use_sum:
                    votes = row_total_votes(row)
                else:
                    # Try explicit total vote cells first
                    tv = None
                    for k in ['total votes', 'total_votes', 'total', 'totalvotes', 'totvotes']:
                        if k in row and row[k].strip() != '':
                            try:
                                tv = int(float(row[k]))
                                break
                            except Exception:
                                tv = None
                    if tv is not None:
                        votes = tv
                    else:
                        votes = row_total_votes(row)
                contest_slug = slugify(contest) + f"_{year}"
                contest_entry = data[year][group].setdefault(contest_slug, {'contest_name':contest,'results':{}})
                county_entry = contest_entry['results'].setdefault(county, {'county':county,'contest':contest,'year':year,'per_choice':Counter(), 'total_votes':0})
                county_entry['per_choice'][(candidate_name, party)] += votes
                county_entry['total_votes'] += votes
                # Debug output for missing candidate names in Council of State contests
                if group == 'council_of_state' and not candidate_name:
                    print(f"[DEBUG] Missing candidate name: contest={contest} county={county} party={party} votes={votes}")
            if debug_names:
                print(f"  First 5 contest names: {list(debug_names)[:5]}")
            if not found_any:
                print(f"  NOTE: No target contests found in {fp} (year: {year})")
            if unmatched_contests:
                print(f"  [DEBUG] Unmatched contests in {fp}: {sorted(unmatched_contests)}")
    # Post-process to compute dem/rep/other etc.
    out = {}
    for year, groups in data.items():
        out_year = {}
        for group_name, contests in groups.items():
            out_group = {}
            for slug, c in contests.items():
                contest_name = c['contest_name']
                results = {}
                for county in sorted(c['results'].keys()):
                    ce = c['results'][county]
                    per_choice = ce['per_choice']
                    total_votes = ce['total_votes']
                    # sum by party
                    party_totals = Counter()
                    candidate_by_party = {}
                    for (choice, party), v in per_choice.items():
                        p = party if party else 'OTHER'
                        party_totals[p] += v
                        # track top candidate per party
                        prev = candidate_by_party.get(p)
                        if prev is None or v > prev[1]:
                            candidate_by_party[p] = (choice, v)
                    dem_votes = party_totals.get('DEM',0)
                    rep_votes = party_totals.get('REP',0)
                    # other votes are everything that's not DEM or REP
                    other_votes = sum(v for p,v in party_totals.items() if p not in ('DEM','REP'))
                    two_party_total = dem_votes + rep_votes
                    margin = rep_votes - dem_votes
                    margin_pct = None
                    if two_party_total>0:
                        margin_pct = (margin / two_party_total) * 100
                        margin_pct = round(margin_pct,2)
                    # winner
                    if margin>0:
                        winner = 'REP'
                    elif margin<0:
                        winner = 'DEM'
                    else:
                        # if tie by two-party, fall back to total votes
                        if rep_votes>dem_votes:
                            winner='REP'
                        elif dem_votes>rep_votes:
                            winner='DEM'
                        else:
                            winner='OTHER'
                    # candidate names
                    dem_candidate = candidate_by_party.get('DEM',[None])[0] if 'DEM' in candidate_by_party else None
                    rep_candidate = candidate_by_party.get('REP',[None])[0] if 'REP' in candidate_by_party else None

                    comp = classify_margin(margin_pct)

                    results[county] = {
                        'county': county,
                        'contest': contest_name,
                        'year': year,
                        'dem_candidate': dem_candidate,
                        'rep_candidate': rep_candidate,
                        'dem_votes': int(dem_votes),
                        'rep_votes': int(rep_votes),
                        'other_votes': int(other_votes),
                        'total_votes': int(total_votes),
                        'two_party_total': int(two_party_total),
                        'margin': int(margin),
                        'margin_pct': margin_pct,
                        'winner': winner,
                        'competitiveness': comp,
                        'all_parties': dict(party_totals)
                    }
                out_group[slug] = {
                    'contest_name': contest_name,
                    'results': results
                }
            out_year[group_name] = out_group
        out[year] = out_year

    # merge with existing if provided
    if existing_path and os.path.exists(existing_path):
        try:
            with open(existing_path,'r',encoding='utf-8') as ef:
                existing = json.load(ef)
        except Exception:
            existing = {}
    else:
        existing = {}

    existing.setdefault('metadata', {})
    existing.setdefault('results_by_year', {})
    # Merge and sort results_by_year chronologically
    existing['results_by_year'].update(out)
    # Sort by year as integer keys (if possible)
    try:
        sorted_years = sorted(existing['results_by_year'].keys(), key=lambda y: int(y))
    except Exception:
        sorted_years = sorted(existing['results_by_year'].keys())
    ordered_results = {y: existing['results_by_year'][y] for y in sorted_years}
    existing['results_by_year'] = ordered_results

    with open(output_path, 'w', encoding='utf-8') as of:
        json.dump(existing, of, indent=2)
    print('Wrote', output_path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-glob', default='data/Congressional_Data/NC_Election_Results/*/results_pct_*_clean*.csv')
    ap.add_argument('--output', default='data/county_level_election_results_2008_2024.json')
    ap.add_argument('--existing', default='data/county_level_election_results_2008_2024.json')
    ap.add_argument('--extract-names', action='store_true', help='Extract all contest names to a text file')
    ap.add_argument('--names-output', default='all_contest_names.txt', help='Output file for contest names')
    args = ap.parse_args()
    if args.extract_names:
        extract_all_contest_names(args.input_glob, args.names_output)
    else:
        aggregate_csv_files(args.input_glob, args.output, args.existing)
