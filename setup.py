import os
import sys
import subprocess
from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        # Step 1: Run the parent install process
        install.run(self)

        # Step 2: Create a virtual environment
        self.create_virtual_env()

        # Step 3: Install dependencies inside the virtual environment
        self.install_dependencies()

        # Step 4: Download NLTK corpora
        self.download_nltk_data()

    def create_virtual_env(self):
        print("\nCreating virtual environment...")
        if not os.path.exists('venv'):
            # Create virtual environment
            subprocess.check_call([sys.executable, '-m', 'venv', 'venv'])
            print("Virtual environment created successfully.")
        else:
            print("Virtual environment already exists.")

    def install_dependencies(self):
        print("\nInstalling dependencies in the virtual environment...")

        # Activate virtual environment
        if os.name == 'nt':
            activate_this = os.path.join('venv', 'Scripts', 'activate')
        else:
            activate_this = os.path.join('venv', 'bin', 'activate')

        # Install dependencies inside the virtual environment
        subprocess.check_call(f'source {activate_this} && pip install -r requirements.txt', shell=True)

    def download_nltk_data(self):
        print("\nDownloading NLTK corpora in the virtual environment...")

        # Activate virtual environment and download NLTK corpora
        if os.name == 'nt':
            activate_this = os.path.join('venv', 'Scripts', 'activate')
        else:
            activate_this = os.path.join('venv', 'bin', 'activate')

        # Download NLTK data inside the virtual environment
        subprocess.check_call(f'source {activate_this} && python -m nltk.downloader all', shell=True)
        print("NLTK corpora downloaded successfully.")


# Setup function
setup(
    name='analyse_pdf_bank_transactions',
    version='0.1',
    description='convert your PDF bank transactions to xls and categorize transactions',
    packages=find_packages(),
    install_requires=[
        'absl-py==0.15.0',
        'antlr4-python3-runtime==4.9.3',
        'astunparse==1.6.3',
        'attrs==23.1.0',
        'black==23.12.0',
        'cachetools==5.3.2',
        'certifi==2022.9.24',
        'chardet==3.0.4',
        'charset-normalizer==3.3.2',
        'click==8.1.7',
        'cloudpickle==3.0.0',
        'colorama==0.4.6',
        'comtypes==1.1.14',
        'contourpy==1.1.1',
        'cycler==0.12.1',
        'Cython==3.0.6',
        'dataclasses==0.6',
        'et-xmlfile==1.1.0',
        'filelock==3.16.1',
        'fire==0.5.0',
        'flatbuffers==1.12',
        'fonttools==4.47.0',
        'fsspec==2024.9.0',
        'future==0.18.3',
        'fuzzywuzzy==0.18.0',
        'fvcore==0.1.5.post20221221',
        'gast==0.3.3',
        'google-auth==2.25.2',
        'google-auth-oauthlib==0.4.6',
        'google-pasta==0.2.0',
        'googletrans==4.0.0rc1',
        'grpcio==1.32.0',
        'h11==0.9.0',
        'h2==3.2.0',
        'h5py==2.10.0',
        'hpack==3.0.0',
        'hstspreload==2022.9.1',
        'httpcore==0.9.1',
        'httpx==0.13.3',
        'huggingface-hub==0.25.1',
        'hydra-core==1.3.2',
        'hyperframe==5.2.0',
        'idna==2.10',
        'imageio==2.33.1',
        'imantics==0.1.12',
        'imgaug==0.4.0',
        'importlib-metadata==7.0.0',
        'importlib-resources==6.1.1',
        'iopath==0.1.10',
        'Jinja2==3.1.4',
        'joblib==1.4.2',
        'jsonschema==4.20.0',
        'jsonschema-specifications==2023.11.2',
        'keras==2.13.1',
        'Keras-Preprocessing==1.1.2',
        'kiwisolver==1.4.5',
        'labelme2coco==0.2.4',
        'lazy_loader==0.3',
        'Levenshtein==0.25.1',
        'libclang==16.0.6',
        'lxml==4.9.3',
        'Markdown==3.5.1',
        'MarkupSafe==2.1.3',
        'matplotlib==3.7.4',
        'MouseInfo==0.1.3',
        'mpmath==1.3.0',
        'mypy-extensions==1.0.0',
        'networkx==3.1',
        'nltk==3.9.1',
        'numpy==1.24.4',
        'oauthlib==3.2.2',
        'omegaconf==2.3.0',
        'opencv-python==4.7.0.72',
        'openpyxl==3.1.5',
        'opt-einsum==3.3.0',
        'packaging==23.2',
        'pandas==2.0.3',
        'pathspec==0.12.1',
        'Pillow==9.2.0',
        'pixellib==0.7.1',
        'pkgutil_resolve_name==1.3.10',
        'platformdirs==4.1.0',
        'portalocker==2.8.2',
        'protobuf==3.20.3',
        'pyasn1==0.5.1',
        'pyasn1-modules==0.3.0',
        'PyAutoGUI==0.9.54',
        'pybboxes==0.1.6',
        'pydot==1.4.2',
        'PyGetWindow==0.0.9',
        'PyMsgBox==1.0.9',
        'pyparsing==3.0.9',
        'PyPDF2==3.0.1',
        'pyperclip==1.8.2',
        'pypiwin32==223',
        'PyQt5==5.15.10',
        'PyQt5-Qt5==5.15.2',
        'PyQt5-sip==12.13.0',
        'PyRect==0.2.0',
        'PyScreeze==0.1.30',
        'pytesseract==0.3.10',
        'python-dateutil==2.8.2',
        'python-dotenv==1.0.1',
        'python-Levenshtein==0.25.1',
        'pyttsx3==2.90',
        'pytweening==1.0.7',
        'pytz==2024.2',
        'PyWavelets==1.4.1',
        'pywin32==304',
        'PyYAML==6.0.1',
        'rapidfuzz==3.9.7',
        'referencing==0.32.0',
        'regex==2024.9.11',
        'requests==2.31.0',
        'requests-oauthlib==1.3.1',
        'rfc3986==1.5.0',
        'rpds-py==0.15.2',
        'rsa==4.9',
        'sahi==0.11.15',
        'scikit-image==0.21.0',
        'scikit-learn==1.3.2',
        'scipy==1.10.1',
        'sentence-transformers==3.1.1',
        'shapely==2.0.2',
        'six==1.15.0',
        'sniffio==1.3.0',
        'sympy==1.13.3',
        'tabulate==0.9.0',
        'termcolor==1.1.0',
        'terminaltables==3.1.10',
        'threadpoolctl==3.5.0',
        'tifffile==2023.7.10',
        'tokenizers==0.20.0',
        'tomli==2.0.1',
        'tqdm==4.66.1',
        'transformers==4.45.1',
        'typing_extensions==4.12.2',
        'tzdata==2024.2',
        'urllib3==2.1.0',
        'Werkzeug==3.0.1',
        'wrapt==1.12.1',
        'XlsxWriter==3.2.0',
        'xmljson==0.2.1',
        'yacs==0.1.8',
        'zipp==3.17.0'
    ],
    python_requires='>=3.8,<3.9',  # Specify Python version 3.8
    cmdclass={
        'install': PostInstallCommand,
    },
)
