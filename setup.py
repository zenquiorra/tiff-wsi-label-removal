from setuptools import setup, find_packages

setup(
    name="tiff-wsi-label-removal",
    version="0.1.5",
    author="Yash Verma",
    author_email="yashv7523@gmail.com",
    description="A tool to remove label pages from TIFF/BigTIFF files...",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/zenquiorra/tiff-wsi-label-removal",
    license="MIT",
    packages=find_packages(),
    install_requires=["tifffile>=2023.4.12"],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "remove-label = tiff_wsi_label_removal.remove_label:main",
        ]
    },
)