from setuptools import setup, find_packages

setup(
    name="zabbix-ai-agent",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyzabbix==1.3.0",
        "pandas==2.1.0",
        "scikit-learn==1.3.0",
        "numpy==1.24.3",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "schedule==1.2.0"
    ],
    entry_points={
        'console_scripts': [
            'zabbix-ai-agent=zabbix_ai_agent:main',
        ],
    },
    author="Sentrait",
    author_email="info@sentrait.com",
    description="Agente de IA para predicción de problemas en Zabbix",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="zabbix, machine learning, monitoring, ai",
    url="https://sentrait.com.uy",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 