"""Prompt système et description de tâche (AD-2, AD-14, AD-15).

Ils ne dépendent que de la méthode, du budget de passes et du paquet de séance : ni du modèle,
ni du pilote, ni du fournisseur (test d'identité). Le prompt système est écrit dans
`system_prompt.md` du dossier de séance, lu tel quel par les deux pilotes.
"""

from __future__ import annotations

import hashlib
import json

from nn_weight_writing.session.tools import Method
from nn_weight_writing.tasks.io import Bundle

SYSTEM_PROMPT_FILE = "system_prompt.md"

_COMMON = """\
Tu participes à une expérience d'écriture directe : tu produis toi-même la solution d'une tâche \
de classification, sans gradient, sans entraînement et sans ajustement statistique.

Règles de la séance :
- Tu n'agis que par les outils fournis ; tu ne vois que la description de tâche et les exemples \
non annotés qui suivent.
- Budget : {pass_budget} passes. Chaque appel de run_on_examples consomme une passe, même si ta \
production est invalide. Une passe renvoie les sorties sur les exemples, jamais un score : les \
exemples n'ont pas d'étiquette.
- Après la dernière passe, seul freeze reste permis.
- Interdits : gradient, entraînement, fonctions d'ajustement (moindres carrés, SVD, \
pseudo-inverse, valeurs propres, solveurs, régression polynomiale, covariance), littéraux \
au-delà de 8 Ko de chaînes ou de 512 nombres. Ces appels sont refusés. La recopie d'exemples \
dans le code est détectée et publiée.
- La séance se termine quand tu appelles freeze, ou dès que tu réponds sans appeler d'outil.
"""

_METHODS = {
    Method.A_LITERAL: """\
Méthode A-littéral : tu écris tous les poids d'un réseau de neurones.
1. declare_network fixe l'architecture (manifeste : encoder, layers de type dense).
2. write_weights écrit les poids par tranches de lignes, autant d'appels que nécessaire.
3. run_on_examples exécute le réseau sur les exemples (une passe).
4. freeze gèle le réseau ; blocks est obligatoire : il partitionne les unités cachées, chaque \
bloc avec sa règle (rule), ses types visés (types, pris dans le vocabulaire) et ses unités.
""",
    Method.A_PROGRAM: """\
Méthode A-programme : tu écris un programme qui construit tous les poids d'un réseau.
1. declare_network fixe l'architecture (manifeste : encoder, layers de type dense).
2. submit_script soumet un script Python (NumPy seul) qui définit build() et renvoie les poids \
L{i}.W et L{i}.b ; il s'exécute dans un bac à sable, ce n'est pas une passe.
3. run_on_examples exécute le réseau sur les exemples (une passe).
4. freeze gèle le réseau ; blocks est obligatoire : il partitionne les unités cachées, chaque \
bloc avec sa règle (rule), ses types visés (types, pris dans le vocabulaire) et ses unités.
""",
    Method.B: """\
Méthode B : tu écris des règles en Python, sans réseau.
1. submit_rules soumet un code (modules re, datetime, math, unicodedata) qui définit \
predict(raw) et renvoie un label ; ce n'est pas une passe.
2. run_on_examples applique les règles aux exemples (une passe).
3. freeze gèle les règles.
""",
}


def system_prompt(method: Method | str, pass_budget: int) -> str:
    method = Method(method)
    return _COMMON.format(pass_budget=pass_budget) + "\n" + _METHODS[method]


def task_message(bundle: Bundle) -> str:
    """Description de tâche : description, encodeur, vocabulaire fermé, exemples non annotés."""
    lines = [
        f"# Tâche : {bundle.task}",
        "",
        bundle.description,
        "",
        f"Encodeur des entrées (fixé par la tâche) : {bundle.encoder}",
        "",
        "## Vocabulaire des types d'erreur visibles",
        "",
        *(f"- {entry.id} : {entry.description}" for entry in bundle.vocabulary),
        "",
        f"## Exemples non annotés ({len(bundle.examples)})",
        "",
        *(json.dumps({"id": e.id, "raw": e.raw}, ensure_ascii=False) for e in bundle.examples),
    ]
    return "\n".join(lines) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
