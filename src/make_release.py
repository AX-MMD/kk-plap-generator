import os
import zipfile

import toml

SRC_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SRC_PATH)

def join_path(*args):
    return os.path.join(SRC_PATH, *args)

def get_app_version(pyproject_file='pyproject.toml'):
    with open(pyproject_file, 'r') as file:
        pyproject_data = toml.load(file)
    return pyproject_data['project']['version']

def zip_directory(zipf, path, base_path, added_files):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.join(base_path, file)
            if arcname not in added_files:
                zipf.write(file_path, arcname)
                added_files.add(arcname)

def create_release_zip(version):
    zip_filename = f'Koikatsu-PLAP-generator.v{version}.zip'
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

    added_files = set()

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:

        # Add /resource and its content
        zip_directory(zipf, join_path(SRC_PATH, 'resources'), 'resources', added_files)

        # Add reference config
        ref_config_path = join_path(SRC_PATH, 'configs', '__app__', 'reference.toml')
        ref_config_arcname = 'configs/__app__/reference.toml'
        if ref_config_arcname not in added_files:
            zipf.write(ref_config_path, ref_config_arcname)
            added_files.add(ref_config_arcname)

        # Add /configs/example.toml
        example_config_path = join_path(SRC_PATH, 'configs', 'example.toml')
        example_config_arcname = 'configs/example.toml'
        if example_config_arcname not in added_files:
            zipf.write(example_config_path, example_config_arcname)
            added_files.add(example_config_arcname)

        # Add EXE
        exe_path = join_path(SRC_PATH, 'bin', 'KoikatsuPlapGenerator.exe')
        exe_arcname = 'KoikatsuPlapGenerator.exe'
        if exe_arcname not in added_files:
            zipf.write(exe_path, exe_arcname)
            added_files.add(exe_arcname)

        # Add EXE dependencies from __internal__
        zip_directory(zipf, join_path(SRC_PATH, 'bin', '__internal__'), '__internal__', added_files)

        # Add LICENSE
        license_path = join_path(PROJECT_DIR, 'LICENSE')
        license_arcname = 'LICENSE'
        if license_arcname not in added_files:
            zipf.write(license_path, license_arcname)
            added_files.add(license_arcname)

        # Add README.md
        readme_path = join_path(PROJECT_DIR, 'README.md')
        readme_arcname = 'README.md'
        if readme_arcname not in added_files:
            zipf.write(readme_path, readme_arcname)
            added_files.add(readme_arcname)

    print(f'Created {zip_filename}')

if __name__ == '__main__':
    version = get_app_version()
    create_release_zip(version)
