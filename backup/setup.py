from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="codegates",
    version="1.0.0",
    author="CodeGates Team",
    description="Hard Gate Assessment tool for code quality validation with JIRA integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        # Core dependencies
        "pydantic>=1.8.0",
        "pathlib2>=2.3.0",
        "requests>=2.25.0",
        
        # FastAPI server dependencies
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        
        # Flask server dependencies (optional)
        "flask>=2.0.0",
        "flask-cors>=4.0.0",
        "flask-limiter>=2.1.0",
        
        # Environment and configuration
        "python-dotenv>=0.19.0",
        
        # LLM integrations (optional)
        "openai>=1.0.0",
        "anthropic>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
        ],
        "docker": [
            "gunicorn>=21.2.0",
            "redis>=4.0.0",
        ]
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "codegates=codegates.cli:main",
            "codegates-server=codegates.api.server:start_server",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 