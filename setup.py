from distutils.core import setup

setup(
    name="wikiparse",
    version="0.1",
    description="Parse wikipedia dump",
    author="Garrin McGoldrick",
    author_email="garrin.mcgoldrick@gmail.com",
    requires=["docopt", "tqdm", "mwparserfromhell"],
    packages=["wikiparse"],
)
