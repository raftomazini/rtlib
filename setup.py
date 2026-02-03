from setuptools import setup, find_packages

setup(
    name="rtlib",
    version="0.1.1",
    description="Biblioteca de utilitarios (Email, OAuth2)",
    author="Rodrigo Tomazini",
    # Encontra automaticamente o pacote 'rtlib' e subpacotes
    packages=find_packages(),
    python_requires='>=3.6',
)
