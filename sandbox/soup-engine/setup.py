"""Compatibility setup.py for older pip editable installs."""

from setuptools import find_packages, setup


setup(
    name="sopilot-rules",
    version="0.1.0",
    description="Standalone deterministic SOUP rule engine for SoPilot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=["pydantic>=2.0"],
    entry_points={
        "console_scripts": [
            "sopilot-validate-soup=sopilot_rules.tools.validate_soup:main",
            "sopilot-rule-gen=sopilot_rules.tools.rule_gen_cli:main",
        ]
    },
)
