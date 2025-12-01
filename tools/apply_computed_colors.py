#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

DATA_PATH = Path(r"c:\Users\Shama\OneDrive\Documents\Course_Materials\CPT-236\Side_Projects\NCLegislativeRealignments\data\county_level_election_results_2000_2024.json")


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


def main():
    if not DATA_PATH.exists():
        print(f"ERROR: data file not found at {DATA_PATH}")
        return

    # Create timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = DATA_PATH.parent / f"county_level_election_results_2000_2024_{timestamp}.json.bak"
    backup_path.write_text(DATA_PATH.read_text(encoding='utf-8'), encoding='utf-8')
    print(f"Created backup: {backup_path}")

    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))

    updated_count = 0
    ry = data.get('results_by_year', {})

    for year, year_obj in ry.items():
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
                        continue

                    if total == 0:
                        continue

                    dem_pct = (dem / total) * 100 if total > 0 else 0
                    rep_pct = (rep / total) * 100 if total > 0 else 0
                    margin = abs(rep_pct - dem_pct)
                    winner = 'R' if rep_pct > dem_pct else 'D'

                    cat, party, code, color = category_color_for_margin(margin, winner)
                    
                    # Ensure competitiveness dict exists
                    if 'competitiveness' not in county_res or not isinstance(county_res['competitiveness'], dict):
                        county_res['competitiveness'] = {}
                    
                    # Update all competitiveness fields
                    comp = county_res['competitiveness']
                    changed = False
                    
                    if comp.get('category') != cat:
                        comp['category'] = cat
                        changed = True
                    if comp.get('party') != party:
                        comp['party'] = party
                        changed = True
                    if comp.get('code') != code:
                        comp['code'] = code
                        changed = True
                    if comp.get('color', '').strip().lower() != color.strip().lower():
                        comp['color'] = color
                        changed = True
                    
                    if changed:
                        updated_count += 1

    # Write updated JSON
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f"Updated {updated_count} county records with computed colors")
    print(f"Saved updated JSON to {DATA_PATH}")


if __name__ == '__main__':
    main()
