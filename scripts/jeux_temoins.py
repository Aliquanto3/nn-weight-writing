"""Génère les jeux de S et S-réservé avec un jeu d'entraînement plus grand (story 1-11).

Usage : uv run python scripts/jeux_temoins.py --seed 0 --train 32768 [--root .]

Même générateur et même graine que `nnww datagen legal` : le réservé (flux k = 0) ne dépend pas
de la taille des autres jeux, il est donc identique octet pour octet à celui de 1-9. Seul le
jeu d'entraînement grandit. Hors dépôt : `data/` et `heldout/` sont ignorés par git.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nn_weight_writing.datasets.legal import Sizes, generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--train", type=int, default=32768)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    for path in generate(seed=args.seed, root=args.root, sizes=Sizes(train=args.train)):
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
