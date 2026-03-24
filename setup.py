from setuptools import setup, find_packages

setup(
    name="skill-system",
    version="1.0.0",
    description="LangGraph + Gemini API 기반 Skills 시스템",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.0.20",
        "google-generativeai>=0.3.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.8",
)