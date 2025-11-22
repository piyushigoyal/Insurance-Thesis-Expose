"""Setup script for Insurance Claims Agent POC."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="insurance-claims-agent",
    version="0.1.0",
    author="Piyushi Goyal",
    description="AI-powered insurance claims processing agent POC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/insurance-claims-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.12.0",
        "anthropic>=0.21.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langchain-anthropic>=0.1.0",
        "streamlit>=1.32.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "kaggle>=1.6.0",
        "sqlalchemy>=2.0.0",
        "scikit-learn>=1.3.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.7.0",
    ],
    entry_points={
        "console_scripts": [
            "insurance-agent=streamlit_app:main",
        ],
    },
)

