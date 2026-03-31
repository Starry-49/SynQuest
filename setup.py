from setuptools import find_packages, setup


setup(
    name="synquest",
    version="0.2.0",
    description="Reusable toolkit for turning domain knowledge sources into structured question banks.",
    long_description=open("README.en.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Starry-49",
    python_requires=">=3.9",
    package_dir={"": "functions"},
    packages=find_packages(where="functions", include=["synquest"]),
    install_requires=[
        "jieba>=0.42.1",
        "rank-bm25>=0.2.2",
        "rapidfuzz>=3.0.0",
        "scikit-learn>=1.4",
        "sentence-transformers>=5.1.2",
    ],
    entry_points={
        "console_scripts": [
            "synquest=synquest.cli:main",
        ]
    },
    license="MIT",
    url="https://github.com/Starry-49/SynQuest",
)
