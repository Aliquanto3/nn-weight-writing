"""Tâches `legal_s`, `legal_s_reserved` (1-9, D5, D7) et `legal_r` (1-13, D6) : description,
vocabulaire, codec."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import numpy as np

from nn_weight_writing.tasks.legal import encoders
from nn_weight_writing.tasks.legal.reference import format_date
from nn_weight_writing.tasks.legal.types import KNOWN, R_EXTRA_TYPES, R_VISIBLE, TYPES, ErrorType

CHARS_ID = "legal.chars@1"
FIELDS_V1_ID = "legal.fields@1"  # runs gelés de 1-11 seulement
FIELDS_ID = "legal.fields@2"
CLASSES = (("real", "référence vraie"), ("fake", "référence fausse"))

HEAD = (
    "Chaque exemple est une référence de décision de justice française : Cour de cassation, "
    "Conseil d'État ou cour d'appel. Toutes sont écrites sous une seule forme, « juridiction "
    "et formation, date, n° numéro », par exemple « Cass. civ. 1re, 12 mars 2015, n° 13-27.123 », "
    "« CE, Sect., 12 mars 2015, n° 381234 » ou « CA Lyon, 12 mars 2015, n° 13/04567 ». La date "
    "s'écrit jour, mois en lettres, année, avec « 1er » pour le premier du mois. Le numéro a la "
    "forme AA-NN.NNN à la Cour de cassation (AA : deux derniers chiffres de l'année "
    "d'enregistrement du pourvoi), six chiffres au Conseil d'État, AA/NNNNN dans une cour "
    "d'appel (AA : deux derniers chiffres de l'année d'enregistrement de l'appel). Le corpus est "
    "arrêté au 1er novembre 2026.\n\n"
    "La moitié des références sont vraies, l'autre moitié fausses. Chaque fausse référence "
    "contient exactement une incohérence, détectable sans base de données."
)
SENTENCE_S = "Son type est l'un des types du vocabulaire ci-dessous."
SENTENCE_RESERVED = "Les types d'incohérence connus sont ceux du vocabulaire ci-dessous."
TAIL = (
    "Classes : `real` (vraie) et `fake` (fausse). Le réseau a deux sorties, dans l'ordre real "
    "puis fake ; la prédiction est la sortie la plus forte, real en cas d'égalité. Les règles "
    "de la méthode B reçoivent la chaîne brute et renvoient `real` ou `fake`.\n\n"
    f"Encodage des entrées du réseau ({CHARS_ID}, fixé par la tâche) : 3 060 valeurs 0 ou 1. La "
    "référence est mise en minuscules, puis découpée à ses deux dernières virgules : l'en-tête "
    "(juridiction et formation), la date, et le numéro, qui suit « n° ». La date est coupée à "
    "ses espaces en jour, mois et année. Cinq champs de caractères, alignés à gauche, sont "
    "remplis position par position et tronqués au-delà de leur longueur : en-tête, 32 positions "
    "à partir de la position 0 ; jour, 3 à partir de 32 ; mois, 9 à partir de 35 ; année, 4 à "
    "partir de 44 ; numéro, 12 à partir de 48 ; soit 60 positions. Chaque position a 51 "
    f"entrées : une par symbole de l'alphabet « {encoders.ALPHABET} » (symboles 0 à 49, "
    "l'espace est le symbole 36), et le symbole 50 pour tout autre caractère. L'entrée d'indice "
    "51 × position + symbole vaut 1 si la position porte ce symbole ; une position vide est "
    "toute à 0."
)


def _vocabulary(
    types: tuple[ErrorType, ...], overrides: dict[str, str] | None = None
) -> tuple[dict, ...]:
    overrides = overrides or {}
    return tuple({"id": t.id, "description": overrides.get(t.id, t.description)} for t in types)


# --- Jeu R (story 1-13, D6) ---------------------------------------------------------------
# `R_CORPUS_DATE` : date d'extraction des vraies (S5), posée par le commit « jeu R figé ». Tant
# qu'elle vaut None, le prompt de R n'existe pas et `nnww session --task legal_r` est refusé.
R_CORPUS_DATE: date | None = None
R_CORPUS_PENDING = "(date d'arrêt du corpus non fixée)"


def r_corpus_text(day: date | None = R_CORPUS_DATE) -> str:
    return format_date(day.day, day.month, day.year) if day is not None else R_CORPUS_PENDING


HEAD_R = (
    "Chaque exemple est une référence de décision de justice française : Cour de cassation ou "
    "Conseil d'État. Toutes sont écrites sous une seule forme, « juridiction et formation, date, "
    "n° numéro », par exemple « Cass. civ. 1re, 12 mars 2015, n° 13-27.123 » ou « CE, Sect., "
    "12 mars 2015, n° 381234 ». Au Conseil d'État, la formation peut aussi être des chambres "
    "réunies (« CE, 3e et 8e ch. réunies ») ou le juge des référés (« CE, juge des référés »). "
    "La date s'écrit jour, mois en lettres, année, avec « 1er » pour le premier du mois. Le "
    "numéro a la forme AA-NN.NNN à la Cour de cassation (AA : deux derniers chiffres de l'année "
    "d'enregistrement du pourvoi), six chiffres au Conseil d'État. Le corpus est arrêté au "
    f"{r_corpus_text()}.\n\n"
    "La moitié des références sont vraies, tirées des bases publiques ; l'autre moitié sont des "
    "références citées par de petits modèles de langage et absentes de ces bases."
)
SENTENCE_R = (
    "Une fausse peut présenter une ou plusieurs incohérences du vocabulaire ci-dessous, une "
    "autre incohérence, ou aucune incohérence visible."
)
R_TYPE_OVERRIDES = (
    ("t06", f"Décision future : date postérieure au {r_corpus_text()}, date d'arrêt du corpus."),
)


@dataclass(frozen=True)
class LegalTask:
    """Mêmes attributs que `ToyTask` pour que les témoins réutilisent `baselines/train.py`."""

    name: str
    sentence: str
    visible: tuple[str, ...]
    classes: tuple[tuple[str, str], ...] = CLASSES
    n_inputs: int = encoders.N_CHARS
    encoder_id: str = CHARS_ID
    prepared_encoder_id: str = FIELDS_ID
    n_prepared_inputs: int = encoders.N_FIELDS_V2
    head: str = HEAD
    # Descriptions remplacées par identifiant (paires, pour que la tâche reste hachable).
    type_overrides: tuple[tuple[str, str], ...] = ()

    @property
    def description(self) -> str:
        return f"{self.head} {self.sentence}\n\n{TAIL}"

    @property
    def vocabulary(self) -> list[dict]:
        types = tuple(t for t in (*TYPES, *R_EXTRA_TYPES) if t.id in self.visible)
        return list(_vocabulary(types, dict(self.type_overrides)))

    @property
    def class_ids(self) -> tuple[str, ...]:
        return tuple(cid for cid, _ in self.classes)

    def encode(self, raw: object) -> np.ndarray:
        return encoders.encode_chars(raw)

    def encode_prepared(self, raw: object) -> np.ndarray:
        return encoders.encode_fields_v2(raw)

    @property
    def legacy_encoders(self) -> dict[str, Callable[[object], np.ndarray]]:
        """Anciennes versions, lues pour mesurer les runs gelés qui les portent (AD-4)."""
        return {FIELDS_V1_ID: encoders.encode_fields}

    def decode(self, outputs: np.ndarray) -> str:
        """`real` ou `fake` : sortie la plus forte, `real` en cas d'égalité."""
        scores = np.asarray(outputs, dtype=np.float32).reshape(-1)
        if scores.shape != (len(self.classes),):
            raise ValueError(f"{self.name} : {scores.size} sorties, 2 attendues")
        return self.class_ids[int(np.argmax(scores))]


TASK_S = LegalTask("legal_s", SENTENCE_S, tuple(t.id for t in TYPES))
TASK_S_RESERVED = LegalTask("legal_s_reserved", SENTENCE_RESERVED, KNOWN)
TASK_R = LegalTask("legal_r", SENTENCE_R, R_VISIBLE, head=HEAD_R, type_overrides=R_TYPE_OVERRIDES)
