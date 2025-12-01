import os
import shutil
import subprocess

def create_deploy_structure():
    """Create deployment directory structure"""
    deploy_dir = 'deploy'
    os.makedirs(deploy_dir, exist_ok=True)
    os.makedirs(os.path.join(deploy_dir, 'styles'), exist_ok=True)
    os.makedirs(os.path.join(deploy_dir, 'scripts'), exist_ok=True)
    os.makedirs(os.path.join(deploy_dir, 'data'), exist_ok=True)

def optimize_and_copy_files():
    """Optimize and copy all necessary files to deploy directory"""
    # Copy and minify CSS
    with open('styles/main.css', 'r', encoding='utf-8') as f:
        css = f.read()
    # Basic CSS minification
    css = '\n'.join(line.strip() for line in css.split('\n') if line.strip())
    with open('deploy/styles/main.css', 'w', encoding='utf-8') as f:
        f.write(css)
    
    # Copy and minify JavaScript
    with open('scripts/map.js', 'r', encoding='utf-8') as f:
        js = f.read()
    # Basic JS minification
    js = '\n'.join(line.strip() for line in js.split('\n') if line.strip() and not line.strip().startswith('//'))
    with open('deploy/scripts/map.js', 'w', encoding='utf-8') as f:
        f.write(js)
    
    # Copy GeoJSON files
    if os.path.exists('data/nc_counties.geojson'):
        shutil.copy2('data/nc_counties.geojson', 'deploy/data/')
    if os.path.exists('data/nc_precincts_enhanced_2024.geojson'):
        shutil.copy2('data/nc_precincts_enhanced_2024.geojson', 'deploy/data/')

def main():
    """Main deployment function"""
    print("Starting deployment process...")
    
    # Create directory structure
    print("Creating directory structure...")
    create_deploy_structure()
    
    # Optimize and copy files
    print("Optimizing and copying files...")
    optimize_and_copy_files()
    
    # Create docs directory
    print("Creating docs directory...")
    docs_dir = 'docs'
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir)
    shutil.copytree('deploy', docs_dir)
    
    print("Deployment package created successfully!")
    print("\nNext steps:")
    print("1. Commit all changes")
    print("2. Push to GitHub")
    print("3. Enable GitHub Pages in repository settings")
    print("4. Set the source to the 'main' branch and '/docs' folder")
    print("5. Your site will be available at https://Tenjin25.github.io/nc-election-analysis")

if __name__ == '__main__':
    main()
