echo "from setuptools import setup, find_packages

setup(
    name='offline-tts-app',
    version='1.0.0',
    author='Your Name',
    description='A 100% free offline text-to-speech desktop application',
    packages=find_packages(),
    install_requires=[
        'pyttsx3>=2.90',
        'pywin32>=306',
        'PyPDF2>=3.0.0',
        'python-docx>=1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'tts-app=main:main',
        ],
    },
)
" > setup.py