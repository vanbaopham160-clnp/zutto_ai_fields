from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="zutto_ai_fields",
    version="0.0.1",
    description="AI-powered field content generation for Frappe",
    author="Zutto Solutions",
    author_email="",
    packages=find_packages(),
    install_requires=install_requires,
    zip_safe=False,
    include_package_data=True,

)