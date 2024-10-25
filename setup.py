from typing import Iterator
from setuptools import setup, find_namespace_packages


def subpackages() -> Iterator[str]:
    # filter to only folders starting with my.
    for p in find_namespace_packages("."):
        if p.startswith("my"):
            yield p


def main() -> None:
    pkg = "HPI-purarue-personal"
    setup(
        name=pkg,
        version="0.1.0",
        license="MIT",
        packages=list(subpackages()),
        package_data={"my": ["py.typed"]},
        zip_safe=False,
        python_requires=">=3.8",
    )


if __name__ == "__main__":
    main()
