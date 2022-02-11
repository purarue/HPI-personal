from typing import Iterator
from setuptools import setup, find_namespace_packages


def subpackages() -> Iterator[str]:
    # make sure subpackages are only in the my/ folder (not in tests or other folders here)
    for p in find_namespace_packages(".", include=("my.*",)):
        if p.startswith("my"):
            yield p


def main() -> None:
    pkg = "HPI-seanbreckenridge-personal"
    setup(
        name=pkg,
        version="0.1.0",
        license="MIT",
        packages=list(subpackages()),
        package_data={pkg: ["py.typed"]},
        zip_safe=False,
        python_requires=">=3.8",
    )


if __name__ == "__main__":
    main()
