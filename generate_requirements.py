import os
import ast
import sys
import importlib.util
import subprocess
import warnings
from importlib.metadata import distribution, PackageNotFoundError

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=SyntaxWarning)

def get_imports(file_path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        
        for encoding in ['utf-8', 'latin-1', 'ascii']:
            try:
                decoded_content = content.decode(encoding)
                tree = ast.parse(decoded_content)
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"Error: Unable to decode file {file_path}")
            return set()
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    imports.add(node.module.split('.')[0])
        
        return imports
    except SyntaxError as e:
        print(f"Syntax error in file {file_path}: {str(e)}")
        return set()
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return set()

def is_third_party(package):
    if package == '__main__':
        return False
    try:
        spec = importlib.util.find_spec(package)
        if spec is None:
            return False
        location = spec.origin if spec.origin else spec.loader.path
        return not location.startswith(sys.prefix) and not location.startswith(sys.base_prefix)
    except (ImportError, AttributeError, ValueError):
        try:
            distribution(package)
            return True
        except PackageNotFoundError:
            return False

def get_installed_version(package):
    try:
        return distribution(package).version
    except PackageNotFoundError:
        return None

def generate_requirements(project_path):
    all_imports = set()
    
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                all_imports.update(get_imports(file_path))
    
    third_party_packages = set(pkg for pkg in all_imports if is_third_party(pkg))
    
    # Add Django and other common packages
    third_party_packages.update(['django', 'gunicorn', 'whitenoise', 'psycopg2-binary'])
    
    with open('requirements.txt', 'w') as req_file:
        for package in sorted(third_party_packages):
            version = get_installed_version(package)
            if version:
                req_file.write(f"{package}=={version}\n")
            else:
                req_file.write(f"{package}\n")
    
    print("requirements.txt file has been generated successfully.")

if __name__ == "__main__":
    project_path = "."  # Current directory, change if needed
    generate_requirements(project_path)