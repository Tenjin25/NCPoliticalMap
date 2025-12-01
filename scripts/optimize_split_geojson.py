import json
import gzip
import os
import math
from shapely.geometry import shape, mapping, MultiPolygon, box
from shapely.ops import unary_union

def split_bbox(bbox, divisions=2):
    """Split a bounding box into smaller regions"""
    minx, miny, maxx, maxy = bbox
    width = maxx - minx
    height = maxy - miny
    
    # Create grid
    regions = []
    for i in range(divisions):
        for j in range(divisions):
            x1 = minx + (width * i / divisions)
            y1 = miny + (height * j / divisions)
            x2 = minx + (width * (i + 1) / divisions)
            y2 = miny + (height * (j + 1) / divisions)
            regions.append((x1, y1, x2, y2))
    
    return regions

def simplify_geojson(geojson_data, tolerance=0.0001, preserve_topology=True):
    """Simplify geometries while preserving topology"""
    features = geojson_data['features']
    simplified_features = []
    
    for feature in features:
        geom = shape(feature['geometry'])
        simplified_geom = geom.simplify(tolerance, preserve_topology=preserve_topology)
        feature['geometry'] = mapping(simplified_geom)
        simplified_features.append(feature)
    
    geojson_data['features'] = simplified_features
    return geojson_data

def split_and_optimize_geojson(geojson_data, output_dir, name_prefix, divisions=2, tolerance=0.0001):
    """Split GeoJSON into regions and optimize each part"""
    print(f"Splitting and optimizing {name_prefix} into {divisions}x{divisions} regions...")
    
    # Calculate overall bounds
    bounds = None
    for feature in geojson_data['features']:
        geom = shape(feature['geometry'])
        if bounds is None:
            bounds = geom.bounds
        else:
            minx = min(bounds[0], geom.bounds[0])
            miny = min(bounds[1], geom.bounds[1])
            maxx = max(bounds[2], geom.bounds[2])
            maxy = max(bounds[3], geom.bounds[3])
            bounds = (minx, miny, maxx, maxy)
    
    # Split into regions
    regions = split_bbox(bounds, divisions)
    
    # Create region index
    region_index = {
        'type': 'FeatureCollection',
        'features': [],
        'metadata': {
            'total_regions': len(regions),
            'divisions': divisions,
            'bounds': bounds,
            'files': []
        }
    }
    
    # Process each region
    for i, region_bounds in enumerate(regions):
        region_box = box(*region_bounds)
        region_features = []
        
        # Find features that intersect this region
        for feature in geojson_data['features']:
            geom = shape(feature['geometry'])
            if geom.intersects(region_box):
                # Clip geometry to region if it extends beyond
                clipped_geom = geom.intersection(region_box)
                if not clipped_geom.is_empty:
                    feature_copy = feature.copy()
                    feature_copy['geometry'] = mapping(clipped_geom)
                    region_features.append(feature_copy)
        
        if region_features:
            # Create region GeoJSON
            region_data = {
                'type': 'FeatureCollection',
                'features': region_features,
                'metadata': {
                    'region_id': i,
                    'bounds': region_bounds
                }
            }
            
            # Optimize region
            optimized_data = simplify_geojson(region_data, tolerance=tolerance)
            
            # Save region
            region_filename = f"{name_prefix}_region_{i}.json.gz"
            output_path = os.path.join(output_dir, region_filename)
            
            with gzip.open(output_path, 'wt') as f:
                json.dump(optimized_data, f)
            
            # Add to index
            region_index['metadata']['files'].append({
                'filename': region_filename,
                'bounds': region_bounds,
                'feature_count': len(region_features)
            })
            
            # Add region boundary to index
            region_index['features'].append({
                'type': 'Feature',
                'geometry': mapping(region_box),
                'properties': {
                    'region_id': i,
                    'filename': region_filename,
                    'feature_count': len(region_features)
                }
            })
    
    # Save index
    index_path = os.path.join(output_dir, f"{name_prefix}_index.json")
    with open(index_path, 'w') as f:
        json.dump(region_index, f)
    
    return region_index

def ensure_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        print(f"Creating directory: {path}")
        os.makedirs(path)
    return path

def read_geojson(filepath):
    """Read GeoJSON file with error handling"""
    print(f"Reading {filepath}...")
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        raise
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file: {filepath}")
        raise
    except Exception as e:
        print(f"Error reading file {filepath}: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        print("\nStarting GeoJSON optimization...")
        
        # Set up directories
        base_dir = os.path.dirname(os.path.dirname(__file__))
        docs_dir = os.path.join(base_dir, 'docs')
        data_dir = os.path.join(docs_dir, 'data')
        gh_pages_dir = ensure_directory(os.path.join(data_dir, 'gh-pages'))
        
        # Create FTP directories
        ftp_dir = ensure_directory(os.path.join(base_dir, 'ftp-data'))
        ftp_geojson_dir = ensure_directory(os.path.join(ftp_dir, 'geojson'))
        ftp_compressed_dir = ensure_directory(os.path.join(ftp_dir, 'compressed'))
    except Exception as e:
        print(f"\nError during initialization: {str(e)}")
        exit(1)
    
    # Create a separate directory for FTP data outside of docs
    ftp_dir = os.path.join(base_dir, 'ftp-data')
    ftp_geojson_dir = os.path.join(ftp_dir, 'geojson')
    ftp_compressed_dir = os.path.join(ftp_dir, 'compressed')
    
    # Create directories if they don't exist
    for directory in [gh_pages_dir, ftp_dir, ftp_geojson_dir, ftp_compressed_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    # Create a README file in the FTP directory
    readme_content = """NC Election Analysis Data Files
=====================================

This directory contains full-resolution data files for FTP deployment:

/geojson/
  - Original, uncompressed GeoJSON files
  - Maximum precision and detail
  - Use these for data analysis or processing

/compressed/
  - Gzip-compressed versions of the GeoJSON files
  - Same data as /geojson/ but compressed
  - Use these for efficient transfer and storage

Note: These files maintain full resolution and all properties.
For web deployment, use the optimized versions in /docs/data/gh-pages/
"""
    
    with open(os.path.join(ftp_dir, 'README.md'), 'w') as f:
        f.write(readme_content)
    
    # Process counties
    print("\nProcessing counties...")
    with open(os.path.join(data_dir, 'nc_counties.geojson'), 'r') as f:
        counties_data = json.load(f)
    
    # Create optimized version for GitHub Pages
    print("Creating optimized version for GitHub Pages...")
    counties_index = split_and_optimize_geojson(
        counties_data,
        gh_pages_dir,
        'counties',
        divisions=2,  # Split into 4 regions (2x2)
        tolerance=0.001  # More aggressive simplification
    )
    
    # Create full-resolution versions for FTP
    print("Creating full-resolution versions for FTP...")
    # Save uncompressed GeoJSON
    with open(os.path.join(ftp_geojson_dir, 'nc_counties.geojson'), 'w') as f:
        json.dump(counties_data, f)
    # Save compressed version
    with gzip.open(os.path.join(ftp_compressed_dir, 'nc_counties.json.gz'), 'wt') as f:
        json.dump(counties_data, f)
    
    # Process precincts
    print("\nProcessing precincts...")
    with open(os.path.join(data_dir, 'nc_precincts_enhanced_2024.geojson'), 'r') as f:
        precincts_data = json.load(f)
    
    # Create optimized version for GitHub Pages
    print("Creating optimized version for GitHub Pages...")
    precincts_index = split_and_optimize_geojson(
        precincts_data,
        gh_pages_dir,
        'precincts',
        divisions=3,  # Split into 9 regions (3x3)
        tolerance=0.0005  # More aggressive simplification
    )
    
    # Create full-resolution versions for FTP
    print("Creating full-resolution versions for FTP...")
    # Save uncompressed GeoJSON
    with open(os.path.join(ftp_geojson_dir, 'nc_precincts_enhanced_2024.geojson'), 'w') as f:
        json.dump(precincts_data, f)
    # Save compressed version
    with gzip.open(os.path.join(ftp_compressed_dir, 'nc_precincts_enhanced_2024.json.gz'), 'wt') as f:
        json.dump(precincts_data, f)
    
    print("\nOptimization complete!")
    print("\nGitHub Pages files (optimized and split):")
    print(f"  {gh_pages_dir}")
    
    print("\nFTP Server files (full resolution):")
    print(f"  Uncompressed GeoJSON: {ftp_geojson_dir}")
    print(f"  Compressed GeoJSON:   {ftp_compressed_dir}")
    
    # Print file sizes
    def get_dir_size(path):
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
        return total / (1024 * 1024)  # Convert to MB
    
    gh_size = get_dir_size(gh_pages_dir)
    ftp_uncompressed_size = get_dir_size(ftp_geojson_dir)
    ftp_compressed_size = get_dir_size(ftp_compressed_dir)
    
    print("\nDirectory Sizes:")
    print(f"  GitHub Pages (optimized): {gh_size:.2f}MB")
    print(f"  FTP Uncompressed: {ftp_uncompressed_size:.2f}MB")
    print(f"  FTP Compressed: {ftp_compressed_size:.2f}MB")
