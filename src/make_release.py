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

def zip_directory(zipf, path, base_path):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.join(base_path, file)
            zipf.write(file_path, arcname)

def create_release_zip(version):
    zip_filename = f'Koikatsu-PLAP-generator.v{version}.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:

        # Add /resource and its content
        zip_directory(zipf, join_path(SRC_PATH, 'resources'), 'resources')

        # Add /configs/__app__ and its content
        zip_directory(zipf, join_path(SRC_PATH, 'configs', '__app__'), 'configs/__app__')

        # Add /configs/example.toml
        zipf.write(join_path(SRC_PATH, 'configs', 'example.toml'), 'configs/example.toml')

        # Add EXE
        zipf.write(join_path(SRC_PATH, 'bin', 'KoikatsuPlapGenerator.exe'), 'KoikatsuPlapGenerator.exe')

        # Add LICENSE
        zipf.write(join_path(PROJECT_DIR, 'LICENSE'), 'LICENSE')

        # Add README.md
        zipf.write(join_path(PROJECT_DIR, 'README.md'), 'README.md')

    print(f'Created {zip_filename}')

if __name__ == '__main__':
    version = get_app_version()
    create_release_zip(version)
