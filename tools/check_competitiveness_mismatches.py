#!/usr/bin/env python3
import json
from pathlib import Path

DATA_PATH = Path(r"c:\Users\Shama\OneDrive\Documents\Course_Materials\CPT-236\Side_Projects\NCLegislativeRealignments\data\county_level_election_results_2000_2024.json")
OUT_PATH = DATA_PATH.parent / 'competitiveness_mismatches.json'


def category_color_for_margin(margin_pct, winner):
    """Returns (category, party, code, color) tuple for the given margin and winner"""
    if margin_pct >= 40:
        cat = 'Annihilation'
        color = '#67000d' if winner == 'R' else '#08306b'
    elif margin_pct >= 30:
        cat = 'Dominant'
        color = '#a50f15' if winner == 'R' else '#08519c'
    elif margin_pct >= 20:
        cat = 'Stronghold'
        color = '#cb181d' if winner == 'R' else '#3182bd'
    elif margin_pct >= 10:
        cat = 'Safe'
        color = '#ef3b2c' if winner == 'R' else '#6baed6'
    elif margin_pct >= 5.5:
        cat = 'Likely'
        color = '#fb6a4a' if winner == 'R' else '#9ecae1'
    elif margin_pct >= 1:
        cat = 'Lean'
        color = '#fcae91' if winner == 'R' else '#c6dbef'
    elif margin_pct >= 0.5:
        cat = 'Tilt'
        color = '#fee8c8' if winner == 'R' else '#e1f5fe'
    else:
        cat = 'Tossup'
        color = '#f7f7f7'
    
    party = 'Republican' if winner == 'R' else 'Democratic'
    code = f"{winner}_{cat.upper()}"
    
    return (cat, party, code, color)


def normalize_color(c):
    if not c:
        return None
    return c.strip().lower()


def main():
    if not DATA_PATH.exists():
        print(f"ERROR: data file not found at {DATA_PATH}")
        return

    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))

    mismatches = []
    total_checked = 0
    total_counties = 0

    ry = data.get('results_by_year') or data.get('results_by_year', {})
    if not ry:
        print('No results_by_year key found at top level; trying top-level structure...')
        ry = data.get('results_by_year', {})

    for year, year_obj in (ry.items() if isinstance(ry, dict) else []):
        if not isinstance(year_obj, dict):
            continue
        for contest_type, contests in year_obj.items():
            if not isinstance(contests, dict):
                continue
            for contest_id, contest in contests.items():
                results = contest.get('results')
                if not results or not isinstance(results, dict):
                    continue
                for county_name, county_res in results.items():
                    dem = county_res.get('dem_votes') or county_res.get('dem') or 0
                    rep = county_res.get('rep_votes') or county_res.get('rep') or 0
                    total = county_res.get('total_votes') or county_res.get('two_party_total') or (dem + rep)
                    try:
                        dem = float(dem)
                        rep = float(rep)
                        total = float(total)
                    except Exception:
                        # if values are not numeric, skip
                        continue

                    if total == 0:
                        continue

                    dem_pct = (dem / total) * 100 if total > 0 else 0
                    rep_pct = (rep / total) * 100 if total > 0 else 0
                    margin = abs(rep_pct - dem_pct)
                    winner = 'R' if rep_pct > dem_pct else 'D'

                    computed_cat, computed_party, computed_code, computed_color = category_color_for_margin(margin, winner)
                    
                    comp_obj = county_res.get('competitiveness') or {}
                    if isinstance(comp_obj, dict):
                        stored_cat = comp_obj.get('category')
                        stored_party = comp_obj.get('party')
                        stored_code = comp_obj.get('code')
                        stored_color = comp_obj.get('color')
                    else:
                        stored_cat = stored_party = stored_code = stored_color = None

                    # Check if any field mismatches
                    mismatch = False
                    if stored_cat != computed_cat:
                        mismatch = True
                    if stored_party != computed_party:
                        mismatch = True
                    if stored_code != computed_code:
                        mismatch = True
                    if normalize_color(stored_color) != normalize_color(computed_color):
                        mismatch = True
                    
                    if mismatch:
                        mismatches.append({
                            'year': year,
                            'contest_type': contest_type,
                            'contest_id': contest_id,
                            'county': county_name,
                            'dem_votes': dem,
                            'rep_votes': rep,
                            'total_votes': total,
                            'dem_pct': round(dem_pct, 3),
                            'rep_pct': round(rep_pct, 3),
                            'margin_pct': round(margin, 3),
                            'winner': winner,
                            'computed': {'category': computed_cat, 'party': computed_party, 'code': computed_code, 'color': computed_color},
                            'stored': {'category': stored_cat, 'party': stored_party, 'code': stored_code, 'color': stored_color}
                        })

                    total_checked += 1

    print(f"Checked {total_checked} county-results. Found {len(mismatches)} mismatches.")
    sample = mismatches[:100]

    OUT_PATH.write_text(json.dumps({'summary': {'checked': total_checked, 'mismatches': len(mismatches)}, 'mismatches_sample': sample}, indent=2), encoding='utf-8')

    print(f"Wrote mismatch report to {OUT_PATH}")
    if sample:
        print('\nSample mismatches:')
        for m in sample[:20]:
            print(f"{m['year']} {m['contest_type']}/{m['contest_id']} - {m['county']}: stored={m['stored']} computed={m['computed']} margin={m['margin_pct']}%")


if __name__ == '__main__':
    main()
