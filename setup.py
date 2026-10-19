from setuptools import setup, find_packages

setup(
    name="gemini-activity-harvester",
    version="0.1.0",
    description="Harvest, deduplicate, and convert Gemini activity history into verified tools and skills",
    author="Alejandro Londono",
    author_email="alejandro@example.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "gemini-activity-harvester=gemini_activity_harvester.cli:main",
        ],
    },
)
