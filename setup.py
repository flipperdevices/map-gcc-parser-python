from distutils.core import setup

setup(
    name="map-parser",
    version="0.1.0",
    author="Flipper & Community",
    author_email="lars+linkermapviz@6xq.net, hello@flipperzero.one",
    license="MIT",
    description="Visualize GNU ld’s linker map with a tree map.",
    url="https://github.com/flipperdevices/map-gcc-parser-python",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.10",
    install_requires=[
        "cxxfilt",
    ],
    entry_points={
        "console_scripts": [
            "map-parser = map-parser.__main__:main",
        ],
    },
)
