import json
import gzip
import os

def optimize_election_data(input_file, output_dir):
    """Split and optimize election data by year"""
    print(f"Reading data from {input_file}...")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create an index file for metadata
    index = {
        'version': '1.0',
        'years': {},
        'metadata': {
            'total_contests': 0,
            'years_covered': []
        }
    }
    
    # Process each year separately
    for year, contests in data.get('results_by_year', {}).items():
        print(f"Processing year {year}...")
        year_data = {
            'contests': {},
            'metadata': {
                'total_contests': 0
            }
        }
        
        for contest_type, contest_data in contests.items():
            for contest_id, details in contest_data.items():
                # Optimize precinct results
                optimized_results = {}
                for precinct_id, precinct_data in details.get('results', {}).items():
                    # Keep only essential fields and round percentages
                    optimized_results[precinct_id] = {
                        'd': precinct_data.get('dem_votes', 0),
                        'r': precinct_data.get('rep_votes', 0),
                        'c': precinct_data.get('county', '')
                    }
                
                year_data['contests'][contest_id] = {
                    'type': contest_type,
                    'results': optimized_results,
                    'meta': {
                        'dc': details.get('dem_candidate', ''),
                        'rc': details.get('rep_candidate', ''),
                        'name': details.get('contest_name', '')
                    }
                }
                year_data['metadata']['total_contests'] += 1
        
        # Save year data compressed
        output_file = os.path.join(output_dir, f'election_data_{year}.json.gz')
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            json.dump(year_data, f)
        
        # Update index
        index['years'][year] = {
            'file': f'election_data_{year}.json.gz',
            'contests': list(year_data['contests'].keys()),
            'total_contests': year_data['metadata']['total_contests']
        }
        index['metadata']['total_contests'] += year_data['metadata']['total_contests']
    
    index['metadata']['years_covered'] = sorted(index['years'].keys())
    
    # Save index
    index_file = os.path.join(output_dir, 'election_data_index.json')
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    
    print("\nOptimization complete!")
    print(f"Years processed: {', '.join(index['metadata']['years_covered'])}")
    print(f"Total contests: {index['metadata']['total_contests']}")
    print(f"\nFiles created in {output_dir}:")
    print(f"- election_data_index.json")
    for year in index['years'].keys():
        print(f"- election_data_{year}.json.gz")

def optimize_precincts(input_file, output_file):
    """Optimize precinct GeoJSON by simplifying and removing unnecessary properties"""
    print(f"Reading precincts from {input_file}...")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Keep only essential properties and simplify structure
    for feature in data['features']:
        props = feature['properties']
        # Keep only essential properties
        feature['properties'] = {
            'id': props.get('GEOID', ''),
            'name': props.get('VTDNAME', ''),
            'county': props.get('COUNTYFP', '')
        }
    
    # Save compressed
    print(f"Saving optimized precincts to {output_file}...")
    with gzip.open(output_file, 'wt', encoding='utf-8') as f:
        json.dump(data, f)

if __name__ == '__main__':
    # Optimize election data
    input_file = 'data/nc_statewide_precinct_comprehensive_2008_2024_UPDATED_MERGED.json'
    output_dir = 'docs/data/elections'
    optimize_election_data(input_file, output_dir)
    
    # Optimize precincts
    precinct_input = 'data/nc_precincts_enhanced_2024.geojson'
    precinct_output = 'docs/data/nc_precincts.json.gz'
    optimize_precincts(precinct_input, precinct_output)
