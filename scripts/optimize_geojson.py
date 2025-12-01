import json
import gzip
import os
from shapely.geometry import shape, mapping

def simplify_geojson(geojson_data, tolerance=0.0001):
    """Simplify geometries while preserving topology"""
    features = geojson_data['features']
    simplified_features = []
    
    for feature in features:
        geom = shape(feature['geometry'])
        simplified_geom = geom.simplify(tolerance, preserve_topology=True)
        feature['geometry'] = mapping(simplified_geom)
        simplified_features.append(feature)
    
    geojson_data['features'] = simplified_features
    return geojson_data

def process_file(input_path, output_path, name):
    # Read input GeoJSON
    print(f"Processing {input_path}...")
    with open(input_path, 'r') as f:
        geojson_data = json.load(f)
    
    # Step 1: Simplify geometries
    print("Simplifying geometries...")
    simplified_data = simplify_geojson(geojson_data)
    
    # Step 2: Compress with gzip
    print("Compressing...")
    with gzip.open(output_path, 'wt') as f:
        json.dump(simplified_data, f)
    
    # Print size reduction
    original_size = os.path.getsize(input_path) / (1024 * 1024)
    final_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Size reduced from {original_size:.2f}MB to {final_size:.2f}MB")

def main():
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
    data_dir = os.path.join(docs_dir, 'data')
    
    # Process counties
    process_file(
        os.path.join(data_dir, 'nc_counties.geojson'),
        os.path.join(data_dir, 'nc_counties.json.gz'),
        'counties'
    )
    
    # Process precincts
    process_file(
        os.path.join(data_dir, 'nc_precincts_enhanced_2024.geojson'),
        os.path.join(data_dir, 'nc_precincts_enhanced_2024.json.gz'),
        'precincts'
    )

if __name__ == '__main__':
    main()
