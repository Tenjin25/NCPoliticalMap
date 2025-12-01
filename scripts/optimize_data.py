import json
import os
from typing import Dict, Any
import gzip

def optimize_election_data(input_file: str, output_file: str) -> None:
    """
    Optimize election data by:
    1. Removing unnecessary fields
    2. Compressing numerical values
    3. Organizing data for efficient access
    """
    print(f"Reading data from {input_file}...")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    optimized_data = {
        'version': '1.0',
        'years': {},
        'metadata': {
            'total_precincts': 0,
            'total_contests': 0,
            'years_covered': []
        }
    }
    
    print("Optimizing data structure...")
    
    # Process each year's data
    for year, contests in data.get('results_by_year', {}).items():
        optimized_data['years'][year] = {}
        
        for contest_type, contest_data in contests.items():
            optimized_data['years'][year][contest_type] = {}
            
            for contest_id, details in contest_data.items():
                results = details.get('results', {})
                
                # Optimize precinct results
                optimized_results = {}
                for precinct_id, precinct_data in results.items():
                    # Only keep essential fields
                    optimized_results[precinct_id] = {
                        'dem': precinct_data.get('dem_votes', 0),
                        'rep': precinct_data.get('rep_votes', 0),
                        'county': precinct_data.get('county', '')
                    }
                
                optimized_data['years'][year][contest_type][contest_id] = {
                    'results': optimized_results,
                    'metadata': {
                        'dem_candidate': details.get('dem_candidate', ''),
                        'rep_candidate': details.get('rep_candidate', ''),
                        'contest_name': details.get('contest_name', '')
                    }
                }
    
    # Update metadata
    total_precincts = len(set(
        precinct_id
        for year_data in optimized_data['years'].values()
        for contest_type in year_data.values()
        for contest in contest_type.values()
        for precinct_id in contest['results'].keys()
    ))
    
    total_contests = sum(
        len([contest_id 
             for contest_type in year_data.values() 
             for contest_id in contest_type.keys()])
        for year_data in optimized_data['years'].values()
    )
    
    optimized_data['metadata'].update({
        'total_precincts': total_precincts,
        'total_contests': total_contests,
        'years_covered': sorted(optimized_data['years'].keys())
    })
    
    # Save compressed data
    print(f"Saving optimized data to {output_file}...")
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with gzip.open(output_file, 'wt', encoding='utf-8') as f:
        json.dump(optimized_data, f)
    
    # Calculate compression stats
    original_size = os.path.getsize(input_file)
    compressed_size = os.path.getsize(output_file)
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"\nOptimization complete!")
    print(f"Original size: {original_size / 1024 / 1024:.2f} MB")
    print(f"Compressed size: {compressed_size / 1024 / 1024:.2f} MB")
    print(f"Compression ratio: {compression_ratio:.1f}%")
    print(f"Total contests: {total_contests}")
    print(f"Total unique precincts: {total_precincts}")
    print(f"Years covered: {', '.join(optimized_data['metadata']['years_covered'])}")

if __name__ == '__main__':
    input_file = 'data/nc_statewide_precinct_comprehensive_2008_2024_UPDATED_MERGED.json'
    output_file = 'deploy/data/election_data.json.gz'
    
    optimize_election_data(input_file, output_file)
