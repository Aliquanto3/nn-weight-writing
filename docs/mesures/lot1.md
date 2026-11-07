# Mesures du lot 1

Généré par `nnww table --lot 1` ; ne pas éditer.

Entrées lues : 87 journaux, 144 `run.json`, 472 `eval*.json` ; empreinte des entrées `c768d61d6afa6f9754156367f29b0307c724ee1849f5a5a62dacb22fd2493bd1`.

Exactitude principale : une tentative non gelée ou en erreur compte 0 ; « Gelées seules » porte sur les tentatives gelées évaluées (k/n). Pourcentages à 1 décimale.

## 1. Cases

| Tâche | Méthode | Taille cible | Modèle | Config | Gelées (k/n) | Exactitude réservée, avant décisions (tentatives comptées ; moy. ± é.-t. [étendue]) | Exactitude réservée après décisions | Gelées seules (moy.) | Par tentative | Vraies | Fausses connues | Tenues à l'écart (HD) | Croisée → legal_r:eval | Croisée → legal_s_reserved:eval | Lisibilité | Paramètres (nominal, médiane) | Taille effective (script, zlib ; médianes) | Passes (moy.) | Facturé ($, somme ; médiane) | Équivalent API ($, somme ; médiane) | Durée (min, médiane) | Drapeaux (séances) | Rejouées (n ; facturé) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| automaton | A-literal | — | claude-sonnet-5-5 | c98a7354 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| automaton | A-literal | — | xiaomi/mimo-v2.6-pro | 9c140854 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| automaton | A-program | — | claude-sonnet-5-5 | 5e7d4fe8 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| automaton | A-program | — | xiaomi/mimo-v2.6-pro | 273ad6f9 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| automaton | B | — | claude-sonnet-5-5 | b5f650a6 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| automaton | B | — | xiaomi/mimo-v2.6-pro | d4523fc4 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| compare | A-literal | — | claude-sonnet-5-5 | c98a7354 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| compare | A-literal | — | xiaomi/mimo-v2.6-pro | 9c140854 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| compare | A-program | — | claude-sonnet-5-5 | 5e7d4fe8 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 1 ; 0,0000 |
| compare | A-program | — | xiaomi/mimo-v2.6-pro | 273ad6f9 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| compare | B | — | claude-sonnet-5-5 | b5f650a6 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| compare | B | — | xiaomi/mimo-v2.6-pro | d4523fc4 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| legal_r | A-literal | 10000 | claude-sonnet-5-5 | e5b6c8b7 | 3/3 | 64,0 ± 6,7 [56,3 ; 69,0] | 64,0 ± 6,7 [56,3 ; 69,0] | 64,0 | t1 69,0 ; t2 66,7 ; t3 56,3 | 100,0 | 28,0 | — | — | — | 37,5 | 9191 | 0 ; 85 | 2,7 | 0,0000 ; 0,0000 | 2,6445 ; 0,5425 | 3,2 | 0 | 0 ; 0,0000 |
| legal_r | A-program | 100000 | claude-sonnet-5-5 | a6e463bc | 3/3 | 69,0 ± 0,6 [68,4 ; 69,5] | 69,0 ± 0,6 [68,4 ; 69,5] | 69,0 | t1 68,4 ; t2 69,0 ; t3 69,5 | 100,0 | 37,9 | — | — | — | 10,8 | 98018 | 1624 ; 673 | 2,0 | 0,0000 ; 0,0000 | 0,4397 ; 0,1684 | 1,4 | 0 | 0 ; 0,0000 |
| legal_r | B | — | claude-sonnet-5-5 | b5f650a6 | 3/3 | 72,4 ± 0,0 [72,4 ; 72,4] | 72,4 ± 0,0 [72,4 ; 72,4] | 72,4 | t1 72,4 ; t2 72,4 ; t3 72,4 | 100,0 | 44,8 | — | — | — | — | 0 | 2067 ; 0 | 0,0 | 0,0000 ; 0,0000 | 0,1267 ; 0,0362 | 0,4 | 2 | 0 ; 0,0000 |
| legal_r | B | — | xiaomi/mimo-v2.6-pro | 22981c11 | 3/3 | 72,8 ± 1,2 [71,8 ; 74,1] | 72,8 ± 1,2 [71,8 ; 74,1] | 72,8 | t1 71,8 ; t2 74,1 ; t3 72,4 | 94,6 | 51,0 | — | — | — | — | 0 | 4122 ; 0 | 2,3 | 0,4559 ; 0,1925 | 0,4559 ; 0,1925 | 29,5 | 0 | 0 ; 0,0000 |
| legal_s | A-literal | 10000 | claude-fable-5-1 | e5b6c8b7 | 1/1 | 87,9 | 87,9 | 87,9 | t1 87,9 | 94,6 | 81,2 | — | 67,8 | 87,9 | 90,0 | 30632 | 0 ; 626 | 4,0 | 0,0000 ; 0,0000 | 14,4980 ; 14,4980 | 43,5 | 0 | 1 ; 0,0000 |
| legal_s | A-literal | 10000 | claude-sonnet-5-5 | e5b6c8b7 | 3/3 | 60,2 ± 5,3 [56,4 ; 66,3] | 60,2 ± 5,3 [56,4 ; 66,3] | 60,2 | t1 58,0 ; t2 66,3 ; t3 56,4 | 99,6 | 20,8 | — | 53,3 | 60,2 | 90,0 | 30632 | 0 ; 235 | 3,3 | 0,0000 ; 0,0000 | 5,1379 ; 2,0296 | 12,0 | 0 | 3 ; 0,0000 |
| legal_s | A-program | 10000 | claude-fable-5-1 | 6155dad5 | 1/1 | 92,2 | 92,2 | 92,2 | t1 92,2 | 96,7 | 87,8 | — | 69,0 | 92,2 | 100,0 | 30632 | 5189 ; 1218 | 1,0 | 0,0000 ; 0,0000 | 2,8725 ; 2,8725 | 8,3 | 0 | 1 ; 0,0000 |
| legal_s | A-program | 10000 | claude-sonnet-5-5 | 6155dad5 | 3/3 | 63,5 ± 4,4 [60,7 ; 68,6] | 63,5 ± 4,4 [60,7 ; 68,6] | 63,5 | t1 68,6 ; t2 60,7 ; t3 61,2 | 94,8 | 32,2 | — | 55,2 | 63,5 | 76,7 | 30632 | 1003 ; 265 | 0,7 | 0,0000 ; 0,0000 | 0,3487 ; 0,1345 | 1,3 | 0 | 0 ; 0,0000 |
| legal_s | A-program | 10000 | xiaomi/mimo-v2.6-pro | 8e081aa1 | 0/1 | 0,0 ± 0,0 [0,0 ; 0,0] | 0,0 | — | t1 - | — | — | — | — | — | — | — | — ; — | 0,0 | 0,1157 ; 0,1157 | 0,1157 ; 0,1157 | 23,5 | 0 | 1 ; 0,0573 |
| legal_s | A-program | 100000 | claude-fable-5-1 | a6e463bc | 1/1 | 98,4 | 98,4 | 98,4 | t1 98,4 | 100,0 | 96,8 | — | 72,4 | 98,4 | 37,4 | 276349 | 8303 ; 4534 | 2,0 | 0,0000 ; 0,0000 | 3,0765 ; 3,0765 | 8,1 | 1 | 1 ; 0,0000 |
| legal_s | A-program | 100000 | claude-sonnet-5-5 | a6e463bc | 3/3 | 91,2 ± 4,8 [85,8 ; 94,9] | 91,2 ± 4,8 [85,8 ; 94,9] | 91,2 | t1 94,9 ; t2 85,8 ; t3 93,0 | 98,7 | 83,8 | — | 69,2 | 91,2 | 46,4 | 245042 | 2816 ; 2288 | 1,3 | 0,0000 ; 0,0000 | 0,8985 ; 0,3059 | 2,7 | 0 | 2 ; 0,0000 |
| legal_s | B | — | claude-fable-5-1 | b5f650a6 | 1/1 | 98,4 | 98,4 | 98,4 | t1 98,4 | 96,8 | 100,0 | — | 72,4 | 98,4 | — | 0 | 3350 ; 0 | 1,0 | 0,0000 ; 0,0000 | 0,3309 ; 0,3309 | 0,6 | 0 | 0 ; 0,0000 |
| legal_s | B | — | claude-sonnet-5-5 | b5f650a6 | 3/3 | 99,1 ± 0,6 [98,4 ; 99,5] | 99,1 ± 0,6 [98,4 ; 99,5] | 99,1 | t1 98,4 ; t2 99,5 ; t3 99,5 | 98,9 | 99,3 | — | 72,4 | 99,1 | — | 0 | 2767 ; 0 | 0,3 | 0,0000 ; 0,0000 | 0,1854 ; 0,0465 | 0,4 | 0 | 0 ; 0,0000 |
| legal_s | B | — | xiaomi/mimo-v2.6-pro | a52ba2e6 | 0/0 | 0,0 ± 0,0 [0,0 ; 0,0] | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| legal_s | B | — | xiaomi/mimo-v2.6-pro | d4523fc4 | 0/0 | 33,1 ± 57,3 [0,0 ; 99,2] | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| legal_s_reserved | A-literal | 10000 | claude-sonnet-5-5 | e5b6c8b7 | 3/3 | 67,3 ± 12,1 [56,4 ; 80,3] | 67,3 ± 12,1 [56,4 ; 80,3] | 67,3 | t1 80,3 ; t2 56,4 ; t3 65,4 | 99,2 | 43,8 | 18,9 | 57,5 | — | 64,0 | 21443 | 0 ; 204 | 2,7 | 0,0000 ; 0,0000 | 4,5248 ; 1,3843 | 8,6 | 0 | 3 ; 0,0000 |
| legal_s_reserved | A-program | 100000 | claude-sonnet-5-5 | a6e463bc | 3/3 | 88,8 ± 0,9 [87,8 ; 89,6] | 88,8 ± 0,9 [87,8 ; 89,6] | 88,8 | t1 89,0 ; t2 89,6 ; t3 87,8 | 99,4 | 97,1 | 40,5 | 69,3 | — | 42,6 | 131711 | 2494 ; 1498 | 2,0 | 0,0000 ; 0,0000 | 0,8992 ; 0,3086 | 2,7 | 1 | 3 ; 0,0000 |
| legal_s_reserved | B | — | claude-sonnet-5-5 | b5f650a6 | 3/3 | 88,7 ± 1,1 [87,4 ; 89,3] | 88,7 ± 1,1 [87,4 ; 89,3] | 88,7 | t1 87,4 ; t2 89,3 ; t3 89,3 | 97,9 | 99,0 | 40,5 | 67,2 | — | — | 0 | 1799 ; 0 | 0,0 | 0,0000 ; 0,0000 | 0,0948 ; 0,0314 | 0,3 | 0 | 0 ; 0,0000 |
| legal_s_reserved | B | — | xiaomi/mimo-v2.6-pro | a52ba2e6 | 0/0 | 59,9 ± 51,9 [0,0 ; 90,0] | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| legal_s_reserved | B | — | xiaomi/mimo-v2.6-pro | d4523fc4 | 0/0 | 0,0 ± 0,0 [0,0 ; 0,0] | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| parity | A-literal | — | claude-sonnet-5-5 | c98a7354 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| parity | A-literal | — | xiaomi/mimo-v2.6-pro | 9c140854 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| parity | A-program | — | claude-sonnet-5-5 | 5e7d4fe8 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| parity | A-program | — | xiaomi/mimo-v2.6-pro | 273ad6f9 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 1 ; 0,0173 |
| parity | B | — | claude-sonnet-5-5 | b5f650a6 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |
| parity | B | — | xiaomi/mimo-v2.6-pro | d4523fc4 | 0/0 | 100,0 | — | — | — | — | — | — | — | — | — | — | — ; — | — | 0,0000 ; — | 0,0000 ; — | — | 0 | 0 ; 0,0000 |

## 2. Témoins C et F

| Tâche | Témoin | Encodeur | Chemin | N | Graines | Exactitude (moy. ± é.-t.) | Par graine (correct/n) | Vraies | Fausses connues | Tenues à l'écart | Croisée → legal_r:eval | Croisée → legal_s_reserved:eval | Statut |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| legal_s | C | legal.chars@1 | — | 64 | 0, 1, 2 | 51,7 ± 0,2 | s0 2073/4000 ; s1 2068/4000 ; s2 2060/4000 | 55,9 | 47,4 | — | 49,2 | 51,7 | comptée |
| legal_s | C | legal.chars@1 | — | 256 | 0, 1, 2 | 55,4 ± 0,2 | s0 2207/4000 ; s1 2220/4000 ; s2 2216/4000 | 54,7 | 56,0 | — | 43,3 | 55,4 | comptée |
| legal_s | C | legal.chars@1 | — | 1024 | 0, 1, 2 | 62,6 ± 0,4 | s0 2509/4000 ; s1 2488/4000 ; s2 2517/4000 | 60,4 | 64,8 | — | 53,4 | 62,6 | comptée |
| legal_s | C | legal.chars@1 | — | 8192 | 0, 1, 2 | 83,7 ± 0,9 | s0 3325/4000 ; s1 3391/4000 ; s2 3332/4000 | 84,4 | 83,1 | — | 59,2 | 83,7 | comptée |
| legal_s | C | legal.chars@1 | — | 32768 | 0, 1, 2 | 94,6 ± 0,1 | s0 3781/4000 ; s1 3784/4000 ; s2 3792/4000 | 96,5 | 92,8 | — | 66,1 | 94,6 | comptée |
| legal_s | F | legal.fields@1 | annexe-fields1 | 64 | 0, 1, 2 | 53,2 ± 0,3 | s0 2121/4000 ; s1 2121/4000 ; s2 2140/4000 | 53,3 | 53,1 | — | 50,0 | 53,2 | annexe |
| legal_s | F | legal.fields@1 | annexe-fields1 | 256 | 0, 1, 2 | 55,6 ± 0,4 | s0 2232/4000 ; s1 2203/4000 ; s2 2232/4000 | 55,9 | 55,2 | — | 47,7 | 55,6 | annexe |
| legal_s | F | legal.fields@1 | annexe-fields1 | 1024 | 0, 1, 2 | 62,3 ± 0,2 | s0 2501/4000 ; s1 2493/4000 ; s2 2486/4000 | 61,2 | 63,5 | — | 57,3 | 62,3 | annexe |
| legal_s | F | legal.fields@1 | annexe-fields1 | 8192 | 0, 1, 2 | 72,0 ± 2,4 | s0 2952/4000 ; s1 2768/4000 ; s2 2914/4000 | 75,2 | 68,7 | — | 63,8 | 72,0 | annexe |
| legal_s | F | legal.fields@1 | annexe-fields1 | 32768 | 0, 1, 2 | 88,2 ± 1,0 | s0 3553/4000 ; s1 3545/4000 ; s2 3482/4000 | 92,9 | 83,4 | — | 68,4 | 88,2 | annexe |
| legal_s | F | legal.fields@2 | — | 64 | 0, 1, 2 | 53,3 ± 0,2 | s0 2123/4000 ; s1 2138/4000 ; s2 2130/4000 | 53,0 | 53,5 | — | 50,4 | 53,3 | comptée |
| legal_s | F | legal.fields@2 | — | 256 | 0, 1, 2 | 56,1 ± 0,5 | s0 2234/4000 ; s1 2235/4000 ; s2 2266/4000 | 58,2 | 54,1 | — | 46,4 | 56,1 | comptée |
| legal_s | F | legal.fields@2 | — | 1024 | 0, 1, 2 | 66,8 ± 0,4 | s0 2662/4000 ; s1 2688/4000 ; s2 2661/4000 | 67,7 | 65,8 | — | 53,8 | 66,8 | comptée |
| legal_s | F | legal.fields@2 | — | 8192 | 0, 1, 2 | 84,1 ± 1,7 | s0 3284/4000 ; s1 3400/4000 ; s2 3407/4000 | 86,0 | 82,2 | — | 60,3 | 84,1 | comptée |
| legal_s | F | legal.fields@2 | — | 32768 | 0, 1, 2 | 93,4 ± 0,5 | s0 3757/4000 ; s1 3729/4000 ; s2 3723/4000 | 94,2 | 92,7 | — | 66,5 | 93,4 | comptée |
| legal_s_reserved | C | legal.chars@1 | — | 64 | 0, 1, 2 | 54,3 ± 0,2 | s0 2170/4000 ; s1 2165/4000 ; s2 2177/4000 | 62,0 | 51,0 | 37,4 | 48,5 | — | comptée |
| legal_s_reserved | C | legal.chars@1 | — | 256 | 0, 1, 2 | 58,0 ± 0,1 | s0 2319/4000 ; s1 2321/4000 ; s2 2323/4000 | 67,2 | 56,7 | 33,1 | 47,3 | — | comptée |
| legal_s_reserved | C | legal.chars@1 | — | 1024 | 0, 1, 2 | 64,2 ± 0,2 | s0 2561/4000 ; s1 2576/4000 ; s2 2567/4000 | 70,6 | 71,2 | 31,1 | 51,9 | — | comptée |
| legal_s_reserved | C | legal.chars@1 | — | 8192 | 0, 1, 2 | 83,6 ± 0,7 | s0 3370/4000 ; s1 3343/4000 ; s2 3318/4000 | 96,8 | 93,8 | 23,6 | 57,1 | — | comptée |
| legal_s_reserved | C | legal.chars@1 | — | 32768 | 0, 1, 2 | 86,1 ± 0,6 | s0 3467/4000 ; s1 3425/4000 ; s2 3434/4000 | 99,6 | 98,4 | 20,8 | 58,0 | — | comptée |
| legal_s_reserved | F | legal.fields@1 | annexe-fields1 | 64 | 0, 1, 2 | 53,2 ± 0,2 | s0 2124/4000 ; s1 2136/4000 ; s2 2124/4000 | 52,6 | 59,0 | 43,4 | 48,7 | — | annexe |
| legal_s_reserved | F | legal.fields@1 | annexe-fields1 | 256 | 0, 1, 2 | 57,7 ± 0,3 | s0 2315/4000 ; s1 2313/4000 ; s2 2291/4000 | 64,5 | 56,7 | 39,1 | 49,2 | — | annexe |
| legal_s_reserved | F | legal.fields@1 | annexe-fields1 | 1024 | 0, 1, 2 | 61,9 ± 0,6 | s0 2452/4000 ; s1 2471/4000 ; s2 2500/4000 | 65,8 | 66,5 | 40,8 | 54,8 | — | annexe |
| legal_s_reserved | F | legal.fields@1 | annexe-fields1 | 8192 | 0, 1, 2 | 70,5 ± 0,8 | s0 2807/4000 ; s1 2856/4000 ; s2 2798/4000 | 79,7 | 75,1 | 33,9 | 55,7 | — | annexe |
| legal_s_reserved | F | legal.fields@1 | annexe-fields1 | 32768 | 0, 1, 2 | 80,5 ± 1,2 | s0 3199/4000 ; s1 3275/4000 ; s2 3185/4000 | 92,7 | 87,1 | 30,8 | 58,2 | — | annexe |
| legal_s_reserved | F | legal.fields@2 | — | 64 | 0, 1, 2 | 54,9 ± 0,2 | s0 2193/4000 ; s1 2205/4000 ; s2 2193/4000 | 58,4 | 56,5 | 41,4 | 51,5 | — | comptée |
| legal_s_reserved | F | legal.fields@2 | — | 256 | 0, 1, 2 | 60,0 ± 0,4 | s0 2412/4000 ; s1 2383/4000 ; s2 2401/4000 | 71,7 | 58,9 | 26,8 | 47,9 | — | comptée |
| legal_s_reserved | F | legal.fields@2 | — | 1024 | 0, 1, 2 | 66,9 ± 0,2 | s0 2674/4000 ; s1 2669/4000 ; s2 2688/4000 | 75,8 | 74,2 | 25,8 | 54,2 | — | comptée |
| legal_s_reserved | F | legal.fields@2 | — | 8192 | 0, 1, 2 | 83,0 ± 0,2 | s0 3331/4000 ; s1 3317/4000 ; s2 3312/4000 | 96,5 | 92,8 | 22,9 | 57,7 | — | comptée |
| legal_s_reserved | F | legal.fields@2 | — | 32768 | 0, 1, 2 | 86,1 ± 0,6 | s0 3423/4000 ; s1 3440/4000 ; s2 3472/4000 | 99,8 | 98,0 | 21,3 | 59,0 | — | comptée |

## 3. C « même réseau »

| Séance d'origine | N | Exactitude de la séance | Réentraîné (moy. ± é.-t.) | Par graine (correct/n) | Écart |
|---|---|---|---|---|---|
| legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z | 8192 | 87,9 | 86,0 ± 1,1 | s0 3489/4000 ; s1 3405/4000 ; s2 3424/4000 | -1,9 |
| legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z | 8192 | 58,0 | 86,0 ± 1,1 | s0 3489/4000 ; s1 3405/4000 ; s2 3424/4000 | 28,0 |
| legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z | 8192 | 66,3 | 86,0 ± 1,1 | s0 3489/4000 ; s1 3405/4000 ; s2 3424/4000 | 19,7 |
| legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z | 8192 | 56,4 | 83,1 ± 1,0 | s0 3278/4000 ; s1 3350/4000 ; s2 3349/4000 | 26,8 |
| legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z | 8192 | 92,2 | 86,0 ± 1,1 | s0 3489/4000 ; s1 3405/4000 ; s2 3424/4000 | -6,2 |
| legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z | 8192 | 68,6 | 86,0 ± 1,1 | s0 3489/4000 ; s1 3405/4000 ; s2 3424/4000 | 17,4 |
| legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z | 8192 | 60,7 | 86,0 ± 1,1 | s0 3489/4000 ; s1 3405/4000 ; s2 3424/4000 | 25,3 |
| legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z | 8192 | 61,2 | 86,0 ± 1,1 | s0 3489/4000 ; s1 3405/4000 ; s2 3424/4000 | 24,8 |
| legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z | 8192 | 98,4 | 61,5 ± 20,0 | s0 2000/4000 ; s1 3383/4000 ; s2 2000/4000 | -36,9 |
| legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z | 8192 | 94,9 | 83,8 ± 0,9 | s0 3313/4000 ; s1 3370/4000 ; s2 3378/4000 | -11,1 |
| legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z | 8192 | 85,8 | 83,1 ± 0,9 | s0 3281/4000 ; s1 3346/4000 ; s2 3346/4000 | -2,6 |
| legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z | 8192 | 93,0 | 83,2 ± 0,5 | s0 3350/4000 ; s1 3311/4000 ; s2 3318/4000 | -9,9 |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T070925Z | 8192 | 80,3 | 82,4 ± 2,0 | s0 3209/4000 ; s1 3317/4000 ; s2 3367/4000 | 2,2 |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T072328Z | 8192 | 56,4 | 83,1 ± 1,5 | s0 3354/4000 ; s1 3361/4000 ; s2 3257/4000 | 26,7 |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T072852Z | 8192 | 65,4 | 83,3 ± 0,5 | s0 3321/4000 ; s1 3357/4000 ; s2 3322/4000 | 18,0 |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T070108Z | 8192 | 89,0 | 83,6 ± 0,7 | s0 3370/4000 ; s1 3343/4000 ; s2 3318/4000 | -5,4 |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z | 8192 | 89,6 | 82,7 ± 0,4 | s0 3317/4000 ; s1 3287/4000 ; s2 3315/4000 | -7,0 |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T070645Z | 8192 | 87,8 | 82,9 ± 0,5 | s0 3316/4000 ; s1 3298/4000 ; s2 3338/4000 | -4,8 |

## 4. Évaluations croisées

| Dossier | Tâche écrite | Cible | Exactitude | Vraies | Fausses | HD |
|---|---|---|---|---|---|---|
| annexe-fields1/train/legal_s-F-n1024-s0 | legal_s | legal_r:eval | 60,9 | 59,8 | 62,1 | — |
| annexe-fields1/train/legal_s-F-n1024-s0 | legal_s | legal_s_reserved:eval | 62,5 | 60,1 | 68,2 | 58,6 |
| annexe-fields1/train/legal_s-F-n1024-s1 | legal_s | legal_r:eval | 54,6 | 58,6 | 50,6 | — |
| annexe-fields1/train/legal_s-F-n1024-s1 | legal_s | legal_s_reserved:eval | 62,3 | 61,9 | 65,9 | 56,5 |
| annexe-fields1/train/legal_s-F-n1024-s2 | legal_s | legal_r:eval | 56,3 | 51,7 | 60,9 | — |
| annexe-fields1/train/legal_s-F-n1024-s2 | legal_s | legal_s_reserved:eval | 62,2 | 61,6 | 65,4 | 57,4 |
| annexe-fields1/train/legal_s-F-n256-s0 | legal_s | legal_r:eval | 49,4 | 54,0 | 44,8 | — |
| annexe-fields1/train/legal_s-F-n256-s0 | legal_s | legal_s_reserved:eval | 55,8 | 56,9 | 56,8 | 50,6 |
| annexe-fields1/train/legal_s-F-n256-s1 | legal_s | legal_r:eval | 44,8 | 51,7 | 37,9 | — |
| annexe-fields1/train/legal_s-F-n256-s1 | legal_s | legal_s_reserved:eval | 55,1 | 55,5 | 56,6 | 50,9 |
| annexe-fields1/train/legal_s-F-n256-s2 | legal_s | legal_r:eval | 48,9 | 49,4 | 48,3 | — |
| annexe-fields1/train/legal_s-F-n256-s2 | legal_s | legal_s_reserved:eval | 55,8 | 55,4 | 58,4 | 51,8 |
| annexe-fields1/train/legal_s-F-n32768-s0 | legal_s | legal_r:eval | 68,4 | 98,9 | 37,9 | — |
| annexe-fields1/train/legal_s-F-n32768-s0 | legal_s | legal_s_reserved:eval | 88,8 | 94,0 | 89,4 | 72,1 |
| annexe-fields1/train/legal_s-F-n32768-s1 | legal_s | legal_r:eval | 68,4 | 97,7 | 39,1 | — |
| annexe-fields1/train/legal_s-F-n32768-s1 | legal_s | legal_s_reserved:eval | 88,6 | 90,8 | 92,6 | 74,3 |
| annexe-fields1/train/legal_s-F-n32768-s2 | legal_s | legal_r:eval | 68,4 | 89,7 | 47,1 | — |
| annexe-fields1/train/legal_s-F-n32768-s2 | legal_s | legal_s_reserved:eval | 87,1 | 94,0 | 83,9 | 72,4 |
| annexe-fields1/train/legal_s-F-n64-s0 | legal_s | legal_r:eval | 51,7 | 21,8 | 81,6 | — |
| annexe-fields1/train/legal_s-F-n64-s0 | legal_s | legal_s_reserved:eval | 53,0 | 52,0 | 59,0 | 44,1 |
| annexe-fields1/train/legal_s-F-n64-s1 | legal_s | legal_r:eval | 48,9 | 17,2 | 80,5 | — |
| annexe-fields1/train/legal_s-F-n64-s1 | legal_s | legal_s_reserved:eval | 53,0 | 53,7 | 58,7 | 39,6 |
| annexe-fields1/train/legal_s-F-n64-s2 | legal_s | legal_r:eval | 49,4 | 18,4 | 80,5 | — |
| annexe-fields1/train/legal_s-F-n64-s2 | legal_s | legal_s_reserved:eval | 53,5 | 54,1 | 58,6 | 41,4 |
| annexe-fields1/train/legal_s-F-n8192-s0 | legal_s | legal_r:eval | 66,1 | 93,1 | 39,1 | — |
| annexe-fields1/train/legal_s-F-n8192-s0 | legal_s | legal_s_reserved:eval | 73,8 | 77,4 | 74,7 | 61,3 |
| annexe-fields1/train/legal_s-F-n8192-s1 | legal_s | legal_r:eval | 61,5 | 77,0 | 46,0 | — |
| annexe-fields1/train/legal_s-F-n8192-s1 | legal_s | legal_s_reserved:eval | 69,2 | 72,9 | 67,6 | 61,4 |
| annexe-fields1/train/legal_s-F-n8192-s2 | legal_s | legal_r:eval | 63,8 | 89,7 | 37,9 | — |
| annexe-fields1/train/legal_s-F-n8192-s2 | legal_s | legal_s_reserved:eval | 72,9 | 75,4 | 73,6 | 63,5 |
| annexe-fields1/train/legal_s_reserved-F-n1024-s0 | legal_s_reserved | legal_r:eval | 51,7 | 55,2 | 48,3 | — |
| annexe-fields1/train/legal_s_reserved-F-n1024-s1 | legal_s_reserved | legal_r:eval | 56,9 | 55,2 | 58,6 | — |
| annexe-fields1/train/legal_s_reserved-F-n1024-s2 | legal_s_reserved | legal_r:eval | 55,7 | 54,0 | 57,5 | — |
| annexe-fields1/train/legal_s_reserved-F-n256-s0 | legal_s_reserved | legal_r:eval | 47,7 | 59,8 | 35,6 | — |
| annexe-fields1/train/legal_s_reserved-F-n256-s1 | legal_s_reserved | legal_r:eval | 50,6 | 62,1 | 39,1 | — |
| annexe-fields1/train/legal_s_reserved-F-n256-s2 | legal_s_reserved | legal_r:eval | 49,4 | 62,1 | 36,8 | — |
| annexe-fields1/train/legal_s_reserved-F-n32768-s0 | legal_s_reserved | legal_r:eval | 58,6 | 98,9 | 18,4 | — |
| annexe-fields1/train/legal_s_reserved-F-n32768-s1 | legal_s_reserved | legal_r:eval | 58,6 | 100,0 | 17,2 | — |
| annexe-fields1/train/legal_s_reserved-F-n32768-s2 | legal_s_reserved | legal_r:eval | 57,5 | 94,3 | 20,7 | — |
| annexe-fields1/train/legal_s_reserved-F-n64-s0 | legal_s_reserved | legal_r:eval | 50,0 | 40,2 | 59,8 | — |
| annexe-fields1/train/legal_s_reserved-F-n64-s1 | legal_s_reserved | legal_r:eval | 47,7 | 35,6 | 59,8 | — |
| annexe-fields1/train/legal_s_reserved-F-n64-s2 | legal_s_reserved | legal_r:eval | 48,3 | 37,9 | 58,6 | — |
| annexe-fields1/train/legal_s_reserved-F-n8192-s0 | legal_s_reserved | legal_r:eval | 55,2 | 82,8 | 27,6 | — |
| annexe-fields1/train/legal_s_reserved-F-n8192-s1 | legal_s_reserved | legal_r:eval | 55,7 | 88,5 | 23,0 | — |
| annexe-fields1/train/legal_s_reserved-F-n8192-s2 | legal_s_reserved | legal_r:eval | 56,3 | 85,1 | 27,6 | — |
| legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z | legal_s | legal_r:eval | 67,8 | 100,0 | 35,6 | — |
| legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z | legal_s | legal_s_reserved:eval | 87,9 | 94,6 | 92,3 | 59,2 |
| legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z | legal_s | legal_r:eval | 53,4 | 100,0 | 6,9 | — |
| legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z | legal_s | legal_s_reserved:eval | 58,0 | 99,6 | 22,1 | 4,8 |
| legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z | legal_s | legal_r:eval | 56,3 | 100,0 | 12,6 | — |
| legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z | legal_s | legal_s_reserved:eval | 66,3 | 99,1 | 31,9 | 36,5 |
| legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z | legal_s | legal_r:eval | 50,0 | 100,0 | 0,0 | — |
| legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z | legal_s | legal_s_reserved:eval | 56,4 | 100,0 | 19,0 | 0,0 |
| legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z | legal_s | legal_r:eval | 69,0 | 100,0 | 37,9 | — |
| legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z | legal_s | legal_s_reserved:eval | 92,2 | 96,7 | 95,4 | 72,5 |
| legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z | legal_s | legal_r:eval | 56,3 | 94,3 | 18,4 | — |
| legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z | legal_s | legal_s_reserved:eval | 68,6 | 97,5 | 43,7 | 31,5 |
| legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z | legal_s | legal_r:eval | 52,9 | 88,5 | 17,2 | — |
| legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z | legal_s | legal_s_reserved:eval | 60,7 | 94,0 | 32,5 | 17,6 |
| legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z | legal_s | legal_r:eval | 56,3 | 100,0 | 12,6 | — |
| legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z | legal_s | legal_s_reserved:eval | 61,2 | 92,9 | 34,3 | 20,0 |
| legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z | legal_s | legal_r:eval | 72,4 | 100,0 | 44,8 | — |
| legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z | legal_s | legal_s_reserved:eval | 98,4 | 100,0 | 99,5 | 91,4 |
| legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z | legal_s | legal_r:eval | 69,5 | 100,0 | 39,1 | — |
| legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z | legal_s | legal_s_reserved:eval | 94,9 | 100,0 | 98,1 | 73,6 |
| legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z | legal_s | legal_r:eval | 69,5 | 94,3 | 44,8 | — |
| legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z | legal_s | legal_s_reserved:eval | 85,8 | 98,4 | 77,1 | 65,3 |
| legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z | legal_s | legal_r:eval | 68,4 | 98,9 | 37,9 | — |
| legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z | legal_s | legal_s_reserved:eval | 93,0 | 97,9 | 95,0 | 74,8 |
| legal_s-B-fable-5.1-t1-20261106T060616Z | legal_s | legal_r:eval | 72,4 | 94,3 | 50,6 | — |
| legal_s-B-fable-5.1-t1-20261106T060616Z | legal_s | legal_s_reserved:eval | 98,4 | 96,8 | 100,0 | 100,0 |
| legal_s-B-mimo-v2.6-pro-t3-20261106T063042Z | legal_s | legal_r:eval | 72,4 | 100,0 | 44,8 | — |
| legal_s-B-mimo-v2.6-pro-t3-20261106T063042Z | legal_s | legal_s_reserved:eval | 99,2 | 99,4 | 98,5 | 100,0 |
| legal_s-B-sonnet-5.5-t1-20261106T060304Z | legal_s | legal_r:eval | 72,4 | 100,0 | 44,8 | — |
| legal_s-B-sonnet-5.5-t1-20261106T060304Z | legal_s | legal_s_reserved:eval | 98,4 | 96,8 | 100,0 | 100,0 |
| legal_s-B-sonnet-5.5-t2-20261106T060430Z | legal_s | legal_r:eval | 72,4 | 100,0 | 44,8 | — |
| legal_s-B-sonnet-5.5-t2-20261106T060430Z | legal_s | legal_s_reserved:eval | 99,5 | 100,0 | 98,5 | 100,0 |
| legal_s-B-sonnet-5.5-t3-20261106T060456Z | legal_s | legal_r:eval | 72,4 | 100,0 | 44,8 | — |
| legal_s-B-sonnet-5.5-t3-20261106T060456Z | legal_s | legal_s_reserved:eval | 99,5 | 100,0 | 98,5 | 100,0 |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T070925Z | legal_s_reserved | legal_r:eval | 69,0 | 100,0 | 37,9 | — |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T072328Z | legal_s_reserved | legal_r:eval | 50,0 | 100,0 | 0,0 | — |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T072852Z | legal_s_reserved | legal_r:eval | 53,4 | 100,0 | 6,9 | — |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T070108Z | legal_s_reserved | legal_r:eval | 69,5 | 100,0 | 39,1 | — |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z | legal_s_reserved | legal_r:eval | 69,5 | 100,0 | 39,1 | — |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T070645Z | legal_s_reserved | legal_r:eval | 69,0 | 94,3 | 43,7 | — |
| legal_s_reserved-B-mimo-v2.6-pro-t2-20261106T173223Z | legal_s_reserved | legal_r:eval | 69,5 | 100,0 | 39,1 | — |
| legal_s_reserved-B-mimo-v2.6-pro-t3-20261106T173602Z | legal_s_reserved | legal_r:eval | 69,5 | 100,0 | 39,1 | — |
| legal_s_reserved-B-sonnet-5.5-t1-20261106T060520Z | legal_s_reserved | legal_r:eval | 62,6 | 59,8 | 65,5 | — |
| legal_s_reserved-B-sonnet-5.5-t2-20261106T060535Z | legal_s_reserved | legal_r:eval | 69,5 | 100,0 | 39,1 | — |
| legal_s_reserved-B-sonnet-5.5-t3-20261106T060552Z | legal_s_reserved | legal_r:eval | 69,5 | 100,0 | 39,1 | — |
| train/legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z-retrain-n8192-s0 | legal_s | legal_r:eval | 63,2 | 92,0 | 34,5 | — |
| train/legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 87,2 | 87,4 | 92,9 | 75,4 |
| train/legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z-retrain-n8192-s1 | legal_s | legal_r:eval | 56,3 | 82,8 | 29,9 | — |
| train/legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 85,1 | 88,4 | 86,4 | 72,7 |
| train/legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z-retrain-n8192-s2 | legal_s | legal_r:eval | 59,2 | 92,0 | 26,4 | — |
| train/legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 85,6 | 84,4 | 92,1 | 76,3 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z-retrain-n8192-s0 | legal_s | legal_r:eval | 63,2 | 92,0 | 34,5 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 87,2 | 87,4 | 92,9 | 75,4 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z-retrain-n8192-s1 | legal_s | legal_r:eval | 56,3 | 82,8 | 29,9 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 85,1 | 88,4 | 86,4 | 72,7 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z-retrain-n8192-s2 | legal_s | legal_r:eval | 59,2 | 92,0 | 26,4 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 85,6 | 84,4 | 92,1 | 76,3 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z-retrain-n8192-s0 | legal_s | legal_r:eval | 63,2 | 92,0 | 34,5 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 87,2 | 87,4 | 92,9 | 75,4 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z-retrain-n8192-s1 | legal_s | legal_r:eval | 56,3 | 82,8 | 29,9 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 85,1 | 88,4 | 86,4 | 72,7 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z-retrain-n8192-s2 | legal_s | legal_r:eval | 59,2 | 92,0 | 26,4 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 85,6 | 84,4 | 92,1 | 76,3 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z-retrain-n8192-s0 | legal_s | legal_r:eval | 64,4 | 89,7 | 39,1 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 82,0 | 87,5 | 85,1 | 58,9 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z-retrain-n8192-s1 | legal_s | legal_r:eval | 62,6 | 89,7 | 35,6 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 83,8 | 92,8 | 81,6 | 61,0 |
| train/legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z-retrain-n8192-s2 | legal_s | legal_r:eval | 61,5 | 87,4 | 35,6 | — |
| train/legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 83,7 | 82,3 | 88,7 | 77,9 |
| train/legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z-retrain-n8192-s0 | legal_s | legal_r:eval | 63,2 | 92,0 | 34,5 | — |
| train/legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 87,2 | 87,4 | 92,9 | 75,4 |
| train/legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z-retrain-n8192-s1 | legal_s | legal_r:eval | 56,3 | 82,8 | 29,9 | — |
| train/legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 85,1 | 88,4 | 86,4 | 72,7 |
| train/legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z-retrain-n8192-s2 | legal_s | legal_r:eval | 59,2 | 92,0 | 26,4 | — |
| train/legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 85,6 | 84,4 | 92,1 | 76,3 |
| train/legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z-retrain-n8192-s0 | legal_s | legal_r:eval | 63,2 | 92,0 | 34,5 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 87,2 | 87,4 | 92,9 | 75,4 |
| train/legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z-retrain-n8192-s1 | legal_s | legal_r:eval | 56,3 | 82,8 | 29,9 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 85,1 | 88,4 | 86,4 | 72,7 |
| train/legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z-retrain-n8192-s2 | legal_s | legal_r:eval | 59,2 | 92,0 | 26,4 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 85,6 | 84,4 | 92,1 | 76,3 |
| train/legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z-retrain-n8192-s0 | legal_s | legal_r:eval | 63,2 | 92,0 | 34,5 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 87,2 | 87,4 | 92,9 | 75,4 |
| train/legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z-retrain-n8192-s1 | legal_s | legal_r:eval | 56,3 | 82,8 | 29,9 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 85,1 | 88,4 | 86,4 | 72,7 |
| train/legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z-retrain-n8192-s2 | legal_s | legal_r:eval | 59,2 | 92,0 | 26,4 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 85,6 | 84,4 | 92,1 | 76,3 |
| train/legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z-retrain-n8192-s0 | legal_s | legal_r:eval | 63,2 | 92,0 | 34,5 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 87,2 | 87,4 | 92,9 | 75,4 |
| train/legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z-retrain-n8192-s1 | legal_s | legal_r:eval | 56,3 | 82,8 | 29,9 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 85,1 | 88,4 | 86,4 | 72,7 |
| train/legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z-retrain-n8192-s2 | legal_s | legal_r:eval | 59,2 | 92,0 | 26,4 | — |
| train/legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 85,6 | 84,4 | 92,1 | 76,3 |
| train/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z-retrain-n8192-s0 | legal_s | legal_r:eval | 50,0 | 100,0 | 0,0 | — |
| train/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 50,0 | 100,0 | 0,0 | 0,0 |
| train/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z-retrain-n8192-s1 | legal_s | legal_r:eval | 60,3 | 82,8 | 37,9 | — |
| train/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 84,6 | 88,0 | 87,3 | 68,8 |
| train/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z-retrain-n8192-s2 | legal_s | legal_r:eval | 50,0 | 100,0 | 0,0 | — |
| train/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 50,0 | 100,0 | 0,0 | 0,0 |
| train/legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z-retrain-n8192-s0 | legal_s | legal_r:eval | 60,3 | 85,1 | 35,6 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 82,8 | 84,2 | 87,3 | 69,5 |
| train/legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z-retrain-n8192-s1 | legal_s | legal_r:eval | 62,6 | 79,3 | 46,0 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 84,2 | 83,9 | 90,3 | 73,3 |
| train/legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z-retrain-n8192-s2 | legal_s | legal_r:eval | 64,9 | 90,8 | 39,1 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 84,5 | 85,4 | 88,2 | 74,2 |
| train/legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z-retrain-n8192-s0 | legal_s | legal_r:eval | 59,8 | 82,8 | 36,8 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 82,0 | 83,5 | 87,0 | 67,6 |
| train/legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z-retrain-n8192-s1 | legal_s | legal_r:eval | 59,2 | 90,8 | 27,6 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 83,7 | 86,3 | 86,8 | 69,4 |
| train/legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z-retrain-n8192-s2 | legal_s | legal_r:eval | 61,5 | 83,9 | 39,1 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 83,7 | 84,8 | 88,9 | 69,7 |
| train/legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z-retrain-n8192-s0 | legal_s | legal_r:eval | 62,6 | 88,5 | 36,8 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z-retrain-n8192-s0 | legal_s | legal_s_reserved:eval | 83,8 | 85,4 | 87,3 | 71,8 |
| train/legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z-retrain-n8192-s1 | legal_s | legal_r:eval | 62,1 | 90,8 | 33,3 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z-retrain-n8192-s1 | legal_s | legal_s_reserved:eval | 82,8 | 84,0 | 87,6 | 69,7 |
| train/legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z-retrain-n8192-s2 | legal_s | legal_r:eval | 62,1 | 89,7 | 34,5 | — |
| train/legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z-retrain-n8192-s2 | legal_s | legal_s_reserved:eval | 83,0 | 84,2 | 87,4 | 70,4 |
| train/legal_s-C-n1024-s0 | legal_s | legal_r:eval | 55,2 | 63,2 | 47,1 | — |
| train/legal_s-C-n1024-s0 | legal_s | legal_s_reserved:eval | 62,7 | 59,7 | 70,4 | 56,5 |
| train/legal_s-C-n1024-s1 | legal_s | legal_r:eval | 52,3 | 60,9 | 43,7 | — |
| train/legal_s-C-n1024-s1 | legal_s | legal_s_reserved:eval | 62,2 | 60,8 | 69,2 | 52,6 |
| train/legal_s-C-n1024-s2 | legal_s | legal_r:eval | 52,9 | 46,0 | 59,8 | — |
| train/legal_s-C-n1024-s2 | legal_s | legal_s_reserved:eval | 62,9 | 60,8 | 70,1 | 55,0 |
| train/legal_s-C-n256-s0 | legal_s | legal_r:eval | 44,3 | 41,4 | 47,1 | — |
| train/legal_s-C-n256-s0 | legal_s | legal_s_reserved:eval | 55,2 | 53,3 | 60,1 | 50,9 |
| train/legal_s-C-n256-s1 | legal_s | legal_r:eval | 44,8 | 47,1 | 42,5 | — |
| train/legal_s-C-n256-s1 | legal_s | legal_s_reserved:eval | 55,5 | 55,9 | 59,2 | 47,0 |
| train/legal_s-C-n256-s2 | legal_s | legal_r:eval | 40,8 | 36,8 | 44,8 | — |
| train/legal_s-C-n256-s2 | legal_s | legal_s_reserved:eval | 55,4 | 54,9 | 59,0 | 49,5 |
| train/legal_s-C-n32768-s0 | legal_s | legal_r:eval | 64,9 | 94,3 | 35,6 | — |
| train/legal_s-C-n32768-s0 | legal_s | legal_s_reserved:eval | 94,5 | 96,4 | 98,6 | 80,9 |
| train/legal_s-C-n32768-s1 | legal_s | legal_r:eval | 67,2 | 94,3 | 40,2 | — |
| train/legal_s-C-n32768-s1 | legal_s | legal_s_reserved:eval | 94,6 | 96,1 | 99,0 | 81,4 |
| train/legal_s-C-n32768-s2 | legal_s | legal_r:eval | 66,1 | 90,8 | 41,4 | — |
| train/legal_s-C-n32768-s2 | legal_s | legal_s_reserved:eval | 94,8 | 97,0 | 98,6 | 80,5 |
| train/legal_s-C-n64-s0 | legal_s | legal_r:eval | 50,6 | 21,8 | 79,3 | — |
| train/legal_s-C-n64-s0 | legal_s | legal_s_reserved:eval | 51,8 | 56,6 | 53,6 | 33,9 |
| train/legal_s-C-n64-s1 | legal_s | legal_r:eval | 49,4 | 27,6 | 71,3 | — |
| train/legal_s-C-n64-s1 | legal_s | legal_s_reserved:eval | 51,7 | 55,3 | 54,6 | 35,0 |
| train/legal_s-C-n64-s2 | legal_s | legal_r:eval | 47,7 | 29,9 | 65,5 | — |
| train/legal_s-C-n64-s2 | legal_s | legal_s_reserved:eval | 51,5 | 55,8 | 53,7 | 34,2 |
| train/legal_s-C-n8192-s0 | legal_s | legal_r:eval | 59,2 | 86,2 | 32,2 | — |
| train/legal_s-C-n8192-s0 | legal_s | legal_s_reserved:eval | 83,1 | 85,7 | 87,3 | 67,1 |
| train/legal_s-C-n8192-s1 | legal_s | legal_r:eval | 59,8 | 88,5 | 31,0 | — |
| train/legal_s-C-n8192-s1 | legal_s | legal_s_reserved:eval | 84,8 | 85,7 | 90,3 | 71,2 |
| train/legal_s-C-n8192-s2 | legal_s | legal_r:eval | 58,6 | 83,9 | 33,3 | — |
| train/legal_s-C-n8192-s2 | legal_s | legal_s_reserved:eval | 83,3 | 81,8 | 90,0 | 74,5 |
| train/legal_s-F-n1024-s0 | legal_s | legal_r:eval | 53,4 | 71,3 | 35,6 | — |
| train/legal_s-F-n1024-s0 | legal_s | legal_s_reserved:eval | 66,5 | 68,0 | 71,4 | 52,4 |
| train/legal_s-F-n1024-s1 | legal_s | legal_r:eval | 53,4 | 66,7 | 40,2 | — |
| train/legal_s-F-n1024-s1 | legal_s | legal_s_reserved:eval | 67,2 | 67,8 | 73,9 | 52,0 |
| train/legal_s-F-n1024-s2 | legal_s | legal_r:eval | 54,6 | 69,0 | 40,2 | — |
| train/legal_s-F-n1024-s2 | legal_s | legal_s_reserved:eval | 66,5 | 67,2 | 72,5 | 52,4 |
| train/legal_s-F-n256-s0 | legal_s | legal_r:eval | 43,7 | 35,6 | 51,7 | — |
| train/legal_s-F-n256-s0 | legal_s | legal_s_reserved:eval | 55,9 | 56,8 | 60,1 | 44,4 |
| train/legal_s-F-n256-s1 | legal_s | legal_r:eval | 47,1 | 39,1 | 55,2 | — |
| train/legal_s-F-n256-s1 | legal_s | legal_s_reserved:eval | 55,9 | 58,1 | 58,2 | 44,7 |
| train/legal_s-F-n256-s2 | legal_s | legal_r:eval | 48,3 | 42,5 | 54,0 | — |
| train/legal_s-F-n256-s2 | legal_s | legal_s_reserved:eval | 56,6 | 59,7 | 58,2 | 44,4 |
| train/legal_s-F-n32768-s0 | legal_s | legal_r:eval | 70,1 | 93,1 | 47,1 | — |
| train/legal_s-F-n32768-s0 | legal_s | legal_s_reserved:eval | 93,9 | 95,4 | 97,2 | 82,9 |
| train/legal_s-F-n32768-s1 | legal_s | legal_r:eval | 66,1 | 92,0 | 40,2 | — |
| train/legal_s-F-n32768-s1 | legal_s | legal_s_reserved:eval | 93,2 | 92,8 | 98,1 | 84,5 |
| train/legal_s-F-n32768-s2 | legal_s | legal_r:eval | 63,2 | 93,1 | 33,3 | — |
| train/legal_s-F-n32768-s2 | legal_s | legal_s_reserved:eval | 93,1 | 94,2 | 97,1 | 81,7 |
| train/legal_s-F-n64-s0 | legal_s | legal_r:eval | 50,6 | 19,5 | 81,6 | — |
| train/legal_s-F-n64-s0 | legal_s | legal_s_reserved:eval | 53,1 | 54,1 | 58,8 | 38,6 |
| train/legal_s-F-n64-s1 | legal_s | legal_r:eval | 50,0 | 17,2 | 82,8 | — |
| train/legal_s-F-n64-s1 | legal_s | legal_s_reserved:eval | 53,4 | 52,8 | 61,4 | 39,6 |
| train/legal_s-F-n64-s2 | legal_s | legal_r:eval | 50,6 | 18,4 | 82,8 | — |
| train/legal_s-F-n64-s2 | legal_s | legal_s_reserved:eval | 53,2 | 52,2 | 60,9 | 41,0 |
| train/legal_s-F-n8192-s0 | legal_s | legal_r:eval | 62,6 | 88,5 | 36,8 | — |
| train/legal_s-F-n8192-s0 | legal_s | legal_s_reserved:eval | 82,1 | 84,8 | 85,2 | 67,9 |
| train/legal_s-F-n8192-s1 | legal_s | legal_r:eval | 59,2 | 87,4 | 31,0 | — |
| train/legal_s-F-n8192-s1 | legal_s | legal_s_reserved:eval | 85,0 | 86,9 | 89,4 | 70,4 |
| train/legal_s-F-n8192-s2 | legal_s | legal_r:eval | 59,2 | 86,2 | 32,2 | — |
| train/legal_s-F-n8192-s2 | legal_s | legal_s_reserved:eval | 85,2 | 86,5 | 89,7 | 72,4 |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T070925Z-retrain-n8192-s0 | legal_s_reserved | legal_r:eval | 56,3 | 94,3 | 18,4 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T070925Z-retrain-n8192-s1 | legal_s_reserved | legal_r:eval | 57,5 | 88,5 | 26,4 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T070925Z-retrain-n8192-s2 | legal_s_reserved | legal_r:eval | 55,7 | 94,3 | 17,2 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T072328Z-retrain-n8192-s0 | legal_s_reserved | legal_r:eval | 56,9 | 92,0 | 21,8 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T072328Z-retrain-n8192-s1 | legal_s_reserved | legal_r:eval | 56,9 | 94,3 | 19,5 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T072328Z-retrain-n8192-s2 | legal_s_reserved | legal_r:eval | 55,7 | 94,3 | 17,2 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T072852Z-retrain-n8192-s0 | legal_s_reserved | legal_r:eval | 56,9 | 90,8 | 23,0 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T072852Z-retrain-n8192-s1 | legal_s_reserved | legal_r:eval | 57,5 | 89,7 | 25,3 | — |
| train/legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T072852Z-retrain-n8192-s2 | legal_s_reserved | legal_r:eval | 55,7 | 93,1 | 18,4 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T070108Z-retrain-n8192-s0 | legal_s_reserved | legal_r:eval | 57,5 | 92,0 | 23,0 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T070108Z-retrain-n8192-s1 | legal_s_reserved | legal_r:eval | 58,0 | 93,1 | 23,0 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T070108Z-retrain-n8192-s2 | legal_s_reserved | legal_r:eval | 55,7 | 87,4 | 24,1 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z-retrain-n8192-s0 | legal_s_reserved | legal_r:eval | 56,9 | 92,0 | 21,8 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z-retrain-n8192-s1 | legal_s_reserved | legal_r:eval | 57,5 | 90,8 | 24,1 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z-retrain-n8192-s2 | legal_s_reserved | legal_r:eval | 58,0 | 90,8 | 25,3 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T070645Z-retrain-n8192-s0 | legal_s_reserved | legal_r:eval | 59,8 | 93,1 | 26,4 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T070645Z-retrain-n8192-s1 | legal_s_reserved | legal_r:eval | 58,0 | 92,0 | 24,1 | — |
| train/legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T070645Z-retrain-n8192-s2 | legal_s_reserved | legal_r:eval | 58,6 | 92,0 | 25,3 | — |
| train/legal_s_reserved-C-n1024-s0 | legal_s_reserved | legal_r:eval | 50,6 | 51,7 | 49,4 | — |
| train/legal_s_reserved-C-n1024-s1 | legal_s_reserved | legal_r:eval | 51,7 | 56,3 | 47,1 | — |
| train/legal_s_reserved-C-n1024-s2 | legal_s_reserved | legal_r:eval | 53,4 | 56,3 | 50,6 | — |
| train/legal_s_reserved-C-n256-s0 | legal_s_reserved | legal_r:eval | 46,6 | 70,1 | 23,0 | — |
| train/legal_s_reserved-C-n256-s1 | legal_s_reserved | legal_r:eval | 46,6 | 73,6 | 19,5 | — |
| train/legal_s_reserved-C-n256-s2 | legal_s_reserved | legal_r:eval | 48,9 | 75,9 | 21,8 | — |
| train/legal_s_reserved-C-n32768-s0 | legal_s_reserved | legal_r:eval | 58,6 | 94,3 | 23,0 | — |
| train/legal_s_reserved-C-n32768-s1 | legal_s_reserved | legal_r:eval | 57,5 | 94,3 | 20,7 | — |
| train/legal_s_reserved-C-n32768-s2 | legal_s_reserved | legal_r:eval | 58,0 | 94,3 | 21,8 | — |
| train/legal_s_reserved-C-n64-s0 | legal_s_reserved | legal_r:eval | 48,3 | 54,0 | 42,5 | — |
| train/legal_s_reserved-C-n64-s1 | legal_s_reserved | legal_r:eval | 48,3 | 52,9 | 43,7 | — |
| train/legal_s_reserved-C-n64-s2 | legal_s_reserved | legal_r:eval | 48,9 | 52,9 | 44,8 | — |
| train/legal_s_reserved-C-n8192-s0 | legal_s_reserved | legal_r:eval | 57,5 | 92,0 | 23,0 | — |
| train/legal_s_reserved-C-n8192-s1 | legal_s_reserved | legal_r:eval | 58,0 | 93,1 | 23,0 | — |
| train/legal_s_reserved-C-n8192-s2 | legal_s_reserved | legal_r:eval | 55,7 | 87,4 | 24,1 | — |
| train/legal_s_reserved-F-n1024-s0 | legal_s_reserved | legal_r:eval | 54,6 | 64,4 | 44,8 | — |
| train/legal_s_reserved-F-n1024-s1 | legal_s_reserved | legal_r:eval | 53,4 | 56,3 | 50,6 | — |
| train/legal_s_reserved-F-n1024-s2 | legal_s_reserved | legal_r:eval | 54,6 | 66,7 | 42,5 | — |
| train/legal_s_reserved-F-n256-s0 | legal_s_reserved | legal_r:eval | 48,3 | 62,1 | 34,5 | — |
| train/legal_s_reserved-F-n256-s1 | legal_s_reserved | legal_r:eval | 47,1 | 63,2 | 31,0 | — |
| train/legal_s_reserved-F-n256-s2 | legal_s_reserved | legal_r:eval | 48,3 | 62,1 | 34,5 | — |
| train/legal_s_reserved-F-n32768-s0 | legal_s_reserved | legal_r:eval | 59,8 | 94,3 | 25,3 | — |
| train/legal_s_reserved-F-n32768-s1 | legal_s_reserved | legal_r:eval | 59,8 | 94,3 | 25,3 | — |
| train/legal_s_reserved-F-n32768-s2 | legal_s_reserved | legal_r:eval | 57,5 | 94,3 | 20,7 | — |
| train/legal_s_reserved-F-n64-s0 | legal_s_reserved | legal_r:eval | 51,7 | 49,4 | 54,0 | — |
| train/legal_s_reserved-F-n64-s1 | legal_s_reserved | legal_r:eval | 51,1 | 48,3 | 54,0 | — |
| train/legal_s_reserved-F-n64-s2 | legal_s_reserved | legal_r:eval | 51,7 | 47,1 | 56,3 | — |
| train/legal_s_reserved-F-n8192-s0 | legal_s_reserved | legal_r:eval | 57,5 | 94,3 | 20,7 | — |
| train/legal_s_reserved-F-n8192-s1 | legal_s_reserved | legal_r:eval | 58,0 | 93,1 | 23,0 | — |
| train/legal_s_reserved-F-n8192-s2 | legal_s_reserved | legal_r:eval | 57,5 | 92,0 | 23,0 | — |

## 5. Drapeaux d'audit par séance

| Séance | script_run (signalés / total) | Kinds (count) | Exemples | Jugement |
|---|---|---|---|---|
| legal_r-B-sonnet-5.5-t2-20261107T154153Z | 1 / 1 | fragment_overlap (10) | jr-s00002, jr-s00003, jr-s00020 | maintenue, 2026-11-07 : fragment_overlap jugé vocabulaire de format : les 10 fragments viennent de 3 littéraux de noms de chambre (Cass. civ. 1re, Cass. civ. 2e, Cass. ass. plén.) parmi 50 ; aucun numéro, aucune date, aucune référence d'exemple recopiée |
| legal_r-B-sonnet-5.5-t3-20261107T154616Z | 1 / 1 | fragment_overlap (10) | jr-s00002, jr-s00003, jr-s00020 | maintenue, 2026-11-07 : fragment_overlap jugé vocabulaire de format : les 10 fragments viennent de 3 littéraux de noms de chambre (Cass. civ. 1re, Cass. civ. 2e, Cass. ass. plén.) parmi 52 ; aucun numéro, aucune date, aucune référence d'exemple recopiée |
| legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z | 2 / 2 | fragment_overlap (4) | legal-s00009, legal-s00012, legal-s00013 | maintenue, 2026-11-07 : fragment_overlap jugé vocabulaire de format : les 4 fragments viennent de 3 littéraux de noms de chambre (cass. civ. 1re, 2e, 3e) parmi 258 ; aucun numéro, aucune date, aucune référence d'exemple recopiée |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z | 2 / 2 | fragment_overlap (4) | legal-r00004, legal-r00012, legal-r00020 | maintenue, 2026-11-07 : fragment_overlap jugé vocabulaire de format : les 4 fragments viennent de 3 littéraux de noms de chambre (cass. civ. 1re, 2e, 3e) parmi 57 ; aucun numéro, aucune date, aucune référence d'exemple recopiée |

## 6. Séances

| Séance | Case | Tentative | Graine | Statut | Fin | Détail | Passes | Tours | Refus | Jetons (entrée, sortie, cache lu, cache écrit) | Facturé | Équivalent API | Durée (min) | tree_sha256 | Exactitude |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| automaton-A-literal-mimo-v2.6-pro-t1-20261105T233158Z | automaton/A-literal/None/xiaomi/mimo-v2.6-pro/9c140854 | 1 | 0 | annexe | frozen | — | 1 | 9 | invalid_manifest | 24033, 7516, 104320, 0 | 0,0174 | 0,0174 | 2,6 | e0287d0328f3 | 400/400 (100,0) |
| automaton-A-literal-sonnet-5.5-t1-20261106T042957Z | automaton/A-literal/None/claude-sonnet-5-5/c98a7354 | 1 | 0 | annexe | frozen | — | 1 | 15 | invalid_manifest | 12, 134, 60174, 19054 | 0,0000 | 0,0550 | 0,4 | 9a568da85df1 | 400/400 (100,0) |
| automaton-A-program-mimo-v2.6-pro-t1-20261105T231059Z | automaton/A-program/None/xiaomi/mimo-v2.6-pro/273ad6f9 | 1 | 0 | annexe | frozen | — | 1 | 6 | invalid_manifest, no_network_declared | 74559, 59248, 266880, 0 | 0,0849 | 0,0849 | 21,0 | c59dc680ec73 | 400/400 (100,0) |
| automaton-A-program-sonnet-5.5-t1-20261106T042934Z | automaton/A-program/None/claude-sonnet-5-5/5e7d4fe8 | 1 | 0 | annexe | frozen | — | 1 | 10 | invalid_manifest, no_network_declared | 12, 135, 50182, 17844 | 0,0000 | 0,0510 | 0,3 | 470f53a8b296 | 400/400 (100,0) |
| automaton-B-mimo-v2.6-pro-t1-20261105T233435Z | automaton/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 1 | 0 | annexe | frozen | — | 0 | 2 | — | 7927, 154, 8192, 0 | 0,0036 | 0,0036 | 0,1 | 36722b1043d6 | 400/400 (100,0) |
| automaton-B-sonnet-5.5-t1-20261106T043025Z | automaton/B/None/claude-sonnet-5-5/b5f650a6 | 1 | 0 | annexe | frozen | — | 0 | 2 | — | 2, 32, 1300, 7251 | 0,0000 | 0,0186 | 0,0 | 5cec9fa0f621 | 400/400 (100,0) |
| compare-A-literal-mimo-v2.6-pro-t1-20261105T230436Z | compare/A-literal/None/xiaomi/mimo-v2.6-pro/9c140854 | 1 | 0 | annexe | frozen | — | 2 | 8 | invalid_manifest | 67131, 34104, 171648, 0 | 0,0595 | 0,0595 | 6,2 | b8c0b46c5578 | 400/400 (100,0) |
| compare-A-literal-sonnet-5.5-t1-20261106T042847Z | compare/A-literal/None/claude-sonnet-5-5/c98a7354 | 1 | 0 | annexe | frozen | — | 3 | 23 | invalid_blocks, invalid_manifest, network_has_weights | 20, 149, 134367, 33439 | 0,0000 | 0,0986 | 0,6 | c86a1c4b3643 | 400/400 (100,0) |
| compare-A-program-mimo-v2.6-pro-t1-20261105T225332Z | compare/A-program/None/xiaomi/mimo-v2.6-pro/273ad6f9 | 1 | 0 | annexe | frozen | — | 1 | 5 | invalid_manifest, no_network_declared | 48914, 28977, 112000, 0 | 0,0469 | 0,0469 | 11,1 | 512d7440af08 | 400/400 (100,0) |
| compare-A-program-sonnet-5.5-t1-20261106T042604Z | compare/A-program/None/claude-sonnet-5-5/5e7d4fe8 | 1 | 0 | annexe | error | configuration Claude Code non dédiée : skills présent; plugi | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| compare-A-program-sonnet-5.5-t1-20261106T042737Z | compare/A-program/None/claude-sonnet-5-5/5e7d4fe8 | 1 | 0 | annexe | frozen | — | 1 | 12 | invalid_manifest | 12, 84, 45615, 19159 | 0,0000 | 0,0533 | 0,3 | d523d21bbaa9 | 400/400 (100,0) |
| compare-B-mimo-v2.6-pro-t1-20261105T231047Z | compare/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 1 | 0 | annexe | frozen | — | 1 | 3 | — | 11896, 592, 14208, 0 | 0,0057 | 0,0057 | 0,2 | c0ef47f79723 | 400/400 (100,0) |
| compare-B-sonnet-5.5-t1-20261106T042926Z | compare/B/None/claude-sonnet-5-5/b5f650a6 | 1 | 0 | annexe | frozen | — | 0 | 2 | — | 2, 32, 1300, 6704 | 0,0000 | 0,0172 | 0,0 | 8cc4386a9bc1 | 400/400 (100,0) |
| legal_r-A-literal-1e4-sonnet-5.5-t1-20261107T153237Z | legal_r/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 1 | 0 | comptée | frozen | — | 3 | 129 | invalid_manifest, invalid_weights | 64, 103342, 1884934, 118031 | 0,0000 | 1,6942 | 9,2 | aa675cff7638 | 120/174 (69,0) |
| legal_r-A-literal-1e4-sonnet-5.5-t2-20261107T154325Z | legal_r/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 2 | 1 | comptée | frozen | — | 3 | 46 | invalid_manifest, invalid_weights | 30, 26431, 230608, 30092 | 0,0000 | 0,4078 | 2,8 | 6a91cc18fcef | 116/174 (66,7) |
| legal_r-A-literal-1e4-sonnet-5.5-t3-20261107T154814Z | legal_r/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 3 | 2 | comptée | frozen | — | 2 | 36 | invalid_manifest, invalid_weights | 30, 35670, 284438, 39329 | 0,0000 | 0,5425 | 3,2 | 6224ada6f3c4 | 98/174 (56,3) |
| legal_r-A-program-1e5-sonnet-5.5-t1-20261107T153115Z | legal_r/A-program/100000/claude-sonnet-5-5/a6e463bc | 1 | 0 | comptée | frozen | — | 2 | 13 | invalid_manifest | 12, 9189, 57462, 17696 | 0,0000 | 0,1684 | 1,4 | 0baa35fe232e | 119/174 (68,4) |
| legal_r-A-program-1e5-sonnet-5.5-t2-20261107T154222Z | legal_r/A-program/100000/claude-sonnet-5-5/a6e463bc | 2 | 1 | comptée | frozen | — | 1 | 9 | invalid_manifest | 10, 6306, 44414, 7439 | 0,0000 | 0,0973 | 1,0 | b829bf82c406 | 120/174 (69,0) |
| legal_r-A-program-1e5-sonnet-5.5-t3-20261107T154638Z | legal_r/A-program/100000/claude-sonnet-5-5/a6e463bc | 3 | 2 | comptée | frozen | — | 3 | 16 | invalid_manifest | 14, 11112, 81523, 13682 | 0,0000 | 0,1740 | 1,6 | d48edae36458 | 121/174 (69,5) |
| legal_r-B-mimo-v2.6-pro-t1-20261107T155152Z | legal_r/B/None/xiaomi/mimo-v2.6-pro/22981c11 | 1 | 0 | comptée | frozen | — | 4 | 9 | — | 150832, 156022, 899200, 0 | 0,2046 | 0,2046 | 32,0 | 5707c2a738dd | 125/174 (71,8) |
| legal_r-B-mimo-v2.6-pro-t2-20261107T162355Z | legal_r/B/None/xiaomi/mimo-v2.6-pro/22981c11 | 2 | 1 | comptée | frozen | — | 2 | 5 | — | 148227, 145562, 377600, 0 | 0,1925 | 0,1925 | 29,5 | fd3380c5aea6 | 129/174 (74,1) |
| legal_r-B-mimo-v2.6-pro-t3-20261107T165329Z | legal_r/B/None/xiaomi/mimo-v2.6-pro/22981c11 | 3 | 2 | comptée | frozen | — | 1 | 3 | — | 41888, 46480, 48896, 0 | 0,0588 | 0,0588 | 12,1 | b060676e7987 | 126/174 (72,4) |
| legal_r-B-sonnet-5.5-t1-20261107T153051Z | legal_r/B/None/claude-sonnet-5-5/b5f650a6 | 1 | 0 | comptée | frozen | — | 0 | 5 | — | 4, 2644, 5635, 7540 | 0,0000 | 0,0572 | 0,4 | f6ca233b583c | 126/174 (72,4) |
| legal_r-B-sonnet-5.5-t2-20261107T154153Z | legal_r/B/None/claude-sonnet-5-5/b5f650a6 | 2 | 1 | comptée | frozen | — | 0 | 5 | — | 4, 2385, 10916, 2085 | 0,0000 | 0,0333 | 0,5 | e9bc7a442000 | 126/174 (72,4) |
| legal_r-B-sonnet-5.5-t3-20261107T154616Z | legal_r/B/None/claude-sonnet-5-5/b5f650a6 | 3 | 2 | comptée | frozen | — | 0 | 5 | — | 4, 2604, 10915, 2263 | 0,0000 | 0,0362 | 0,3 | 686cccb0f52f | 126/174 (72,4) |
| legal_s-A-literal-1e4-fable-5.1-t1-20261106T062258Z | legal_s/A-literal/10000/claude-fable-5-1/e5b6c8b7 | 1 | 0 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z | legal_s/A-literal/10000/claude-fable-5-1/e5b6c8b7 | 1 | 0 | comptée | frozen | — | 4 | 131 | invalid_manifest | 548, 213394, 1433104, 173225 | 0,0000 | 14,4980 | 43,5 | 7f05e7376d89 | 3517/4000 (87,9) |
| legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062248Z | legal_s/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 1 | 0 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z | legal_s/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 1 | 0 | comptée | frozen | — | 2 | 129 | invalid_manifest, invalid_weights | 78, 123624, 2427431, 137627 | 0,0000 | 2,0296 | 12,0 | 95dd2f72a4a8 | 2318/4000 (58,0) |
| legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T062249Z | legal_s/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 2 | 1 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z | legal_s/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 2 | 1 | comptée | frozen | — | 6 | 137 | invalid_manifest, invalid_weights | 64, 144881, 2577187, 164821 | 0,0000 | 2,3659 | 14,5 | 3125fd4e066e | 2651/4000 (66,3) |
| legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T062250Z | legal_s/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 3 | 2 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z | legal_s/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 3 | 2 | comptée | frozen | — | 2 | 68 | invalid_manifest, invalid_weights | 38, 48332, 501329, 52195 | 0,0000 | 0,7423 | 4,7 | 796de55fc506 | 2254/4000 (56,4) |
| legal_s-A-program-1e4-fable-5.1-t1-20261106T062256Z | legal_s/A-program/10000/claude-fable-5-1/6155dad5 | 1 | 0 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z | legal_s/A-program/10000/claude-fable-5-1/6155dad5 | 1 | 0 | comptée | frozen | — | 1 | 16 | invalid_manifest | 226, 38109, 230709, 45358 | 0,0000 | 2,8725 | 8,3 | 7d6068a85273 | 3689/4000 (92,2) |
| legal_s-A-program-1e4-mimo-v2.6-pro-t1-20261106T174235Z | legal_s/A-program/10000/xiaomi/mimo-v2.6-pro/8e081aa1 | 1 | 0 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 3736, 64000, 384, 0 | 0,0573 | 0,0573 | 12,4 | — | - |
| legal_s-A-program-1e4-mimo-v2.6-pro-t1-20261106T213133Z | legal_s/A-program/10000/xiaomi/mimo-v2.6-pro/8e081aa1 | 1 | 0 | comptée | error | réponse tronquée (length) à 131072 jetons | 0 | 1 | — | 3736, 131072, 384, 0 | 0,1157 | 0,1157 | 23,5 | — | - |
| legal_s-A-program-1e4-mimo-v2.6-pro-t2-20261106T175503Z | legal_s/A-program/10000/xiaomi/mimo-v2.6-pro/8e081aa1 | 2 | 1 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 24, 64000, 4096, 0 | 0,0557 | 0,0557 | 12,6 | — | - |
| legal_s-A-program-1e4-mimo-v2.6-pro-t3-20261106T180740Z | legal_s/A-program/10000/xiaomi/mimo-v2.6-pro/8e081aa1 | 3 | 2 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 24, 64000, 4096, 0 | 0,0557 | 0,0557 | 13,0 | — | - |
| legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z | legal_s/A-program/10000/claude-sonnet-5-5/6155dad5 | 1 | 0 | comptée | frozen | — | 1 | 12 | invalid_manifest | 12, 8085, 46325, 14623 | 0,0000 | 0,1440 | 1,3 | fa37afe3957d | 2744/4000 (68,6) |
| legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z | legal_s/A-program/10000/claude-sonnet-5-5/6155dad5 | 2 | 1 | comptée | frozen | — | 0 | 10 | invalid_manifest, no_network_declared | 12, 4638, 48693, 4747 | 0,0000 | 0,0703 | 0,9 | 9349c0f5816a | 2429/4000 (60,7) |
| legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z | legal_s/A-program/10000/claude-sonnet-5-5/6155dad5 | 3 | 2 | comptée | frozen | — | 1 | 12 | invalid_manifest, no_network_declared | 14, 8668, 79001, 9966 | 0,0000 | 0,1345 | 1,4 | cdb8b3b29ef2 | 2449/4000 (61,2) |
| legal_s-A-program-1e5-fable-5.1-t1-20261106T062257Z | legal_s/A-program/100000/claude-fable-5-1/a6e463bc | 1 | 0 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z | legal_s/A-program/100000/claude-fable-5-1/a6e463bc | 1 | 0 | comptée | frozen | — | 2 | 23 | invalid_manifest | 290, 40631, 271344, 48709 | 0,0000 | 3,0765 | 8,1 | b98d8fb50199 | 3935/4000 (98,4) |
| legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z | legal_s/A-program/100000/claude-sonnet-5-5/a6e463bc | 1 | 0 | comptée | frozen | — | 1 | 11 | invalid_manifest | 12, 19343, 97644, 25665 | 0,0000 | 0,3059 | 2,7 | c6e604e6ea4f | 3797/4000 (94,9) |
| legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062247Z | legal_s/A-program/100000/claude-sonnet-5-5/a6e463bc | 2 | 1 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z | legal_s/A-program/100000/claude-sonnet-5-5/a6e463bc | 2 | 1 | comptée | frozen | — | 1 | 11 | invalid_manifest | 12, 15959, 87649, 17550 | 0,0000 | 0,2386 | 2,4 | 878f421c995f | 3430/4000 (85,8) |
| legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062248Z | legal_s/A-program/100000/claude-sonnet-5-5/a6e463bc | 3 | 2 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z | legal_s/A-program/100000/claude-sonnet-5-5/a6e463bc | 3 | 2 | comptée | frozen | — | 2 | 15 | invalid_blocks, invalid_manifest | 14, 23602, 126531, 26343 | 0,0000 | 0,3541 | 3,1 | ffc26c6b9b79 | 3722/4000 (93,0) |
| legal_s-B-fable-5.1-t1-20261106T060616Z | legal_s/B/None/claude-fable-5-1/b5f650a6 | 1 | 0 | comptée | frozen | — | 1 | 8 | — | 98, 2777, 22749, 9267 | 0,0000 | 0,3309 | 0,6 | 4610a350f3c4 | 3935/4000 (98,4) |
| legal_s-B-mimo-v2.6-pro-t1-20261106T060302Z | legal_s/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 1 | 1 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 3906, 64000, 0, 0 | 0,0574 | 0,0574 | 13,8 | — | - |
| legal_s-B-mimo-v2.6-pro-t1-20261106T165222Z | legal_s/B/None/xiaomi/mimo-v2.6-pro/a52ba2e6 | 1 | 0 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 3906, 64000, 0, 0 | 0,0574 | 0,0574 | 11,4 | — | - |
| legal_s-B-mimo-v2.6-pro-t2-20261106T061711Z | legal_s/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 2 | 2 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 66, 64000, 3840, 0 | 0,0557 | 0,0557 | 13,1 | — | - |
| legal_s-B-mimo-v2.6-pro-t2-20261106T170346Z | legal_s/B/None/xiaomi/mimo-v2.6-pro/a52ba2e6 | 2 | 1 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 66, 64000, 3840, 0 | 0,0557 | 0,0557 | 11,6 | — | - |
| legal_s-B-mimo-v2.6-pro-t3-20261106T063042Z | legal_s/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 3 | 3 | annexe | frozen | — | 1 | 3 | — | 57954, 57832, 68352, 0 | 0,0758 | 0,0758 | 11,4 | 76ffecbfcd86 | 3968/4000 (99,2) |
| legal_s-B-mimo-v2.6-pro-t3-20261106T171527Z | legal_s/B/None/xiaomi/mimo-v2.6-pro/a52ba2e6 | 3 | 2 | annexe | pass_budget | l'agent a rendu la main sans geler | 0 | 1 | — | 66, 58909, 3840, 0 | 0,0513 | 0,0513 | 10,3 | — | - |
| legal_s-B-sonnet-5.5-t1-20261106T060304Z | legal_s/B/None/claude-sonnet-5-5/b5f650a6 | 1 | 0 | comptée | frozen | — | 1 | 8 | — | 6, 5042, 14772, 10948 | 0,0000 | 0,0957 | 0,6 | 42ed8281c2b5 | 3935/4000 (98,4) |
| legal_s-B-sonnet-5.5-t2-20261106T060430Z | legal_s/B/None/claude-sonnet-5-5/b5f650a6 | 2 | 1 | comptée | frozen | — | 0 | 5 | — | 4, 3374, 11055, 2920 | 0,0000 | 0,0465 | 0,4 | bbec2fa7d1a7 | 3980/4000 (99,5) |
| legal_s-B-sonnet-5.5-t3-20261106T060456Z | legal_s/B/None/claude-sonnet-5-5/b5f650a6 | 3 | 2 | comptée | frozen | — | 0 | 5 | — | 4, 3092, 11055, 2791 | 0,0000 | 0,0432 | 0,4 | 60ec8ab4bdb5 | 3980/4000 (99,5) |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T062254Z | legal_s_reserved/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 1 | 0 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T070925Z | legal_s_reserved/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 1 | 0 | comptée | frozen | — | 2 | 110 | invalid_manifest, invalid_weights | 50, 146646, 2039414, 157300 | 0,0000 | 2,2997 | 14,0 | a97c5c988706 | 3211/4000 (80,3) |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T062255Z | legal_s_reserved/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 2 | 1 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T072328Z | legal_s_reserved/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 2 | 1 | comptée | frozen | — | 2 | 76 | invalid_manifest, invalid_weights | 36, 55212, 503786, 59562 | 0,0000 | 0,8408 | 5,4 | d3dc599beb24 | 2255/4000 (56,4) |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T062255Z | legal_s_reserved/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 3 | 2 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T072852Z | legal_s_reserved/A-literal/10000/claude-sonnet-5-5/e5b6c8b7 | 3 | 2 | comptée | frozen | — | 4 | 70 | invalid_manifest, invalid_weights | 44, 88678, 1047822, 98164 | 0,0000 | 1,3843 | 8,6 | bfb08692fdf9 | 2615/4000 (65,4) |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T062251Z | legal_s_reserved/A-program/100000/claude-sonnet-5-5/a6e463bc | 1 | 0 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T070108Z | legal_s_reserved/A-program/100000/claude-sonnet-5-5/a6e463bc | 1 | 0 | comptée | frozen | — | 2 | 15 | invalid_blocks, invalid_manifest | 14, 19504, 121904, 25848 | 0,0000 | 0,3106 | 2,9 | af6e8902511f | 3559/4000 (89,0) |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T062252Z | legal_s_reserved/A-program/100000/claude-sonnet-5-5/a6e463bc | 2 | 1 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z | legal_s_reserved/A-program/100000/claude-sonnet-5-5/a6e463bc | 2 | 1 | comptée | frozen | — | 1 | 12 | invalid_manifest | 12, 18920, 95549, 20274 | 0,0000 | 0,2799 | 2,7 | d7a389134393 | 3585/4000 (89,6) |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T062253Z | legal_s_reserved/A-program/100000/claude-sonnet-5-5/a6e463bc | 3 | 2 | rejouée | error | configuration Claude Code non dédiée : plugins présent : ['p | 0 | 0 | — | 0, 0, 0, 0 | 0,0000 | 0,0000 | 0,0 | — | - |
| legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T070645Z | legal_s_reserved/A-program/100000/claude-sonnet-5-5/a6e463bc | 3 | 2 | comptée | frozen | — | 3 | 21 | invalid_blocks, invalid_manifest | 18, 19718, 152838, 24036 | 0,0000 | 0,3086 | 2,6 | f6aaa0a97337 | 3511/4000 (87,8) |
| legal_s_reserved-B-mimo-v2.6-pro-t1-20261106T064206Z | legal_s_reserved/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 1 | 1 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 3430, 64000, 256, 0 | 0,0572 | 0,0572 | 12,6 | — | - |
| legal_s_reserved-B-mimo-v2.6-pro-t1-20261106T172547Z | legal_s_reserved/B/None/xiaomi/mimo-v2.6-pro/a52ba2e6 | 1 | 0 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 3686, 64000, 0, 0 | 0,0573 | 0,0573 | 6,6 | — | - |
| legal_s_reserved-B-mimo-v2.6-pro-t2-20261106T065445Z | legal_s_reserved/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 2 | 2 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 3686, 64000, 0, 0 | 0,0573 | 0,0573 | 14,8 | — | - |
| legal_s_reserved-B-mimo-v2.6-pro-t2-20261106T173223Z | legal_s_reserved/B/None/xiaomi/mimo-v2.6-pro/a52ba2e6 | 2 | 1 | annexe | frozen | — | 1 | 3 | — | 33706, 34636, 43392, 0 | 0,0450 | 0,0450 | 3,6 | 1b8efec5d39d | 3589/4000 (89,7) |
| legal_s_reserved-B-mimo-v2.6-pro-t3-20261106T070932Z | legal_s_reserved/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 3 | 3 | annexe | error | réponse tronquée (length) à 64000 jetons | 0 | 1 | — | 102, 64000, 3584, 0 | 0,0557 | 0,0557 | 14,0 | — | - |
| legal_s_reserved-B-mimo-v2.6-pro-t3-20261106T173602Z | legal_s_reserved/B/None/xiaomi/mimo-v2.6-pro/a52ba2e6 | 3 | 2 | annexe | frozen | — | 1 | 3 | — | 58828, 54882, 61440, 0 | 0,0736 | 0,0736 | 6,5 | 48fe41d6796a | 3600/4000 (90,0) |
| legal_s_reserved-B-sonnet-5.5-t1-20261106T060520Z | legal_s_reserved/B/None/claude-sonnet-5-5/b5f650a6 | 1 | 0 | comptée | frozen | — | 0 | 4 | — | 4, 1683, 6707, 5100 | 0,0000 | 0,0379 | 0,2 | 86323191bb9c | 3496/4000 (87,4) |
| legal_s_reserved-B-sonnet-5.5-t2-20261106T060535Z | legal_s_reserved/B/None/claude-sonnet-5-5/b5f650a6 | 2 | 1 | comptée | frozen | — | 0 | 4 | — | 4, 1866, 10465, 1441 | 0,0000 | 0,0255 | 0,3 | 757bb2870ccc | 3572/4000 (89,3) |
| legal_s_reserved-B-sonnet-5.5-t3-20261106T060552Z | legal_s_reserved/B/None/claude-sonnet-5-5/b5f650a6 | 3 | 2 | comptée | frozen | — | 0 | 5 | — | 4, 2284, 10462, 1876 | 0,0000 | 0,0314 | 0,3 | d970f38f8852 | 3574/4000 (89,3) |
| parity-A-literal-mimo-v2.6-pro-t1-20261105T224942Z | parity/A-literal/None/xiaomi/mimo-v2.6-pro/9c140854 | 1 | 0 | annexe | frozen | — | 1 | 9 | invalid_manifest | 28012, 13545, 136192, 0 | 0,0245 | 0,0245 | 3,3 | 74522504d5b5 | 400/400 (100,0) |
| parity-A-literal-sonnet-5.5-t1-20261106T042814Z | parity/A-literal/None/claude-sonnet-5-5/c98a7354 | 1 | 0 | annexe | frozen | — | 1 | 14 | invalid_manifest | 12, 65, 47254, 19578 | 0,0000 | 0,0543 | 0,3 | 568a7b77e619 | 400/400 (100,0) |
| parity-A-program-mimo-v2.6-pro-t1-20261105T224224Z | parity/A-program/None/xiaomi/mimo-v2.6-pro/273ad6f9 | 1 | 0 | annexe | pass_budget | l'agent a rendu la main sans geler | 0 | 1 | — | 7883, 16000, 0, 0 | 0,0173 | 0,0173 | 4,2 | — | - |
| parity-A-program-mimo-v2.6-pro-t1-20261105T224746Z | parity/A-program/None/xiaomi/mimo-v2.6-pro/273ad6f9 | 1 | 0 | annexe | frozen | — | 1 | 9 | invalid_manifest, no_network_declared | 19040, 7985, 109312, 0 | 0,0156 | 0,0156 | 1,8 | 5d38406970ed | 400/400 (100,0) |
| parity-A-program-sonnet-5.5-t1-20261106T042528Z | parity/A-program/None/claude-sonnet-5-5/5e7d4fe8 | 1 | 0 | annexe | frozen | — | 1 | 10 | invalid_manifest, no_network_declared | 10, 64, 37740, 18873 | 0,0000 | 0,0516 | 0,3 | 8c9110f28ee7 | 400/400 (100,0) |
| parity-B-mimo-v2.6-pro-t1-20261105T225302Z | parity/B/None/xiaomi/mimo-v2.6-pro/d4523fc4 | 1 | 0 | annexe | frozen | — | 1 | 3 | — | 12358, 667, 15744, 0 | 0,0060 | 0,0060 | 0,2 | 5ec521c21527 | 400/400 (100,0) |
| parity-B-sonnet-5.5-t1-20261106T042840Z | parity/B/None/claude-sonnet-5-5/b5f650a6 | 1 | 0 | annexe | frozen | — | 0 | 2 | — | 4, 56, 8233, 8331 | 0,0000 | 0,0222 | 0,1 | 8256ddb7dda1 | 400/400 (100,0) |

## 7. Coûts du lot et registre

| Modèle | Pilote | Facturé ($) | Équivalent API ($) |
|---|---|---|---|
| claude-fable-5-1 | claude_code | 0,0000 | 20,7778 |
| claude-sonnet-5-5 | claude_code | 0,0000 | 15,7221 |
| xiaomi/mimo-v2.6-pro | api | 1,7210 | 1,7210 |
| **Total** | — | 1,7210 | 38,2210 |
| Registre (closed) | — | 1,7295 | 38,2295 |
| Écart (journaux − registre) | — | -0,0085 | -0,0085 |

Facturé du lot : 1,7210 $ sur un plafond de 100,0000 $ (1,7 %) ; l'équivalent API n'est pas plafonné.

Séances absentes du registre : 0.

Lignes du registre sans journal : 3 (live-1-6-mimo-v2.6-pro-20261105T221315Z, live-1-6-mimo-v2.6-pro-20261105T222836Z, probe-1-2).

## 8. Configurations

| Config | driver | provider | effort | max_tokens | pass_budget | sampling | protocol_sha256 | system_prompt_sha256 |
|---|---|---|---|---|---|---|---|---|
| 22981c11 | api | openrouter | medium | 131072 | 20 | {} | 0d753121ff3b | fa5f8335a67e |
| 273ad6f9 | api | openrouter | — | — | 20 | {} | 0d753121ff3b | e1008446f32a |
| 5e7d4fe8 | claude_code | subscription | medium | — | 20 | {} | 0d753121ff3b | e1008446f32a |
| 6155dad5 | claude_code | subscription | medium | — | 20 | {} | 0d753121ff3b | 642242ce15e9 |
| 8e081aa1 | api | openrouter | medium | — | 20 | {} | 0d753121ff3b | 642242ce15e9 |
| 9c140854 | api | openrouter | — | — | 20 | {} | 0d753121ff3b | 70cb856e9bdc |
| a52ba2e6 | api | openrouter | medium | — | 20 | {} | 0d753121ff3b | fa5f8335a67e |
| a6e463bc | claude_code | subscription | medium | — | 20 | {} | 0d753121ff3b | f0595997baec |
| b5f650a6 | claude_code | subscription | medium | — | 20 | {} | 0d753121ff3b | fa5f8335a67e |
| c98a7354 | claude_code | subscription | medium | — | 20 | {} | 0d753121ff3b | 70cb856e9bdc |
| d4523fc4 | api | openrouter | — | — | 20 | {} | 0d753121ff3b | fa5f8335a67e |
| e5b6c8b7 | claude_code | subscription | medium | — | 20 | {} | 0d753121ff3b | 072713b7a11a |

## 9. Décisions appliquées

| Portée | Statut | Audit | Date | Motif | Référence | Artefacts visés |
|---|---|---|---|---|---|---|
| group:path=annexe-fields1 | annexe | — | 2026-11-07 | F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot) | docs/experiences/1-11-temoins-c-f.md | 30 |
| group:task=automaton | annexe | — | 2026-11-07 | séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe | docs/experiences/1-8-jouet-sonnet.md, 1-8-jouet-mimo.md | 6 |
| group:task=compare | annexe | — | 2026-11-07 | séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe | docs/experiences/1-8-jouet-sonnet.md, 1-8-jouet-mimo.md | 7 |
| group:task=legal_s,config=8e081aa1 | annexe | — | 2026-11-07 | MiMo A-programme 10⁴, étape 2 (64000 jetons, effort medium, tronquées ×3) : déjà mis en annexe par 1-10 ; seul l'essai de l'étape 3 (même config, entrée [[session]] ci-dessus) compte | docs/experiences/1-10-s-mimo.md, annexe 2, section A | 3 |
| group:task=legal_s,config=a52ba2e6 | annexe | — | 2026-11-07 | MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : réglage remplacé par l'étape 3, déjà mis en annexe par 1-10 | docs/experiences/1-10-s-mimo.md, annexe 2 | 3 |
| group:task=legal_s,config=d4523fc4 | annexe | — | 2026-11-07 | MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10 ; B legal_s t3 (3968/4000) cité en annexe du rapport, hors case | docs/experiences/1-10-s-mimo.md, annexe 1 | 3 |
| group:task=legal_s_reserved,config=a52ba2e6 | annexe | — | 2026-11-07 | MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : déjà mis en annexe par 1-10 ; B t2 et t3 gelées (89,7 et 90,0 %) citées en annexe du rapport, hors case | docs/experiences/1-10-s-mimo.md, annexe 2 | 3 |
| group:task=legal_s_reserved,config=d4523fc4 | annexe | — | 2026-11-07 | MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10 | docs/experiences/1-10-s-mimo.md, annexe 1 | 3 |
| group:task=parity | annexe | — | 2026-11-07 | séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe | docs/experiences/1-8-jouet-sonnet.md, 1-8-jouet-mimo.md | 7 |
| session:legal_r-B-mimo-v2.6-pro-t2-20261107T162355Z | maintenue | — | 2026-11-07 | rappel c00 de 13/48 jugé indice générique, pas mémoire : rules.py ne contient aucune référence ni numéro d'exemple ; il marque fausses les numéros de pourvoi d'allure fabriquée (multiple de 1000 ou de 100, trois chiffres égaux, chiffres consécutifs, répétition du numéro de chambre), au prix de 10 vraies manquées ; exactitude au-dessus du plafond de la grille gardée et lue comme telle | 1-13, séances signalées (alerte D8) ; frozen/rules.py, fonction _suspicious_num | 1 |
| session:legal_r-B-sonnet-5.5-t2-20261107T154153Z | maintenue | judged | 2026-11-07 | fragment_overlap jugé vocabulaire de format : les 10 fragments viennent de 3 littéraux de noms de chambre (Cass. civ. 1re, Cass. civ. 2e, Cass. ass. plén.) parmi 50 ; aucun numéro, aucune date, aucune référence d'exemple recopiée | 1-13, séances signalées ; journal, événement script_run ; frozen/rules.py | 1 |
| session:legal_r-B-sonnet-5.5-t3-20261107T154616Z | maintenue | judged | 2026-11-07 | fragment_overlap jugé vocabulaire de format : les 10 fragments viennent de 3 littéraux de noms de chambre (Cass. civ. 1re, Cass. civ. 2e, Cass. ass. plén.) parmi 52 ; aucun numéro, aucune date, aucune référence d'exemple recopiée | 1-13, séances signalées ; journal, événement script_run ; frozen/rules.py | 1 |
| session:legal_s-A-program-1e4-mimo-v2.6-pro-t1-20261106T213133Z | maintenue | — | 2026-11-07 | confirmé : l'essai de l'étape 3 (131072 jetons, effort medium, graine envoyée), réglage retenu par 1-10, compte pour la tentative 1 ; la séance de l'étape 2 de même config (max_tokens non journalisé) passe en annexe avec son groupe | docs/experiences/1-10-s-mimo.md, réglage retenu (étape 3) | 1 |
| session:legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z | maintenue | judged | 2026-11-07 | fragment_overlap jugé vocabulaire de format : les 4 fragments viennent de 3 littéraux de noms de chambre (cass. civ. 1re, 2e, 3e) parmi 258 ; aucun numéro, aucune date, aucune référence d'exemple recopiée | spec 1-14, jugements à rendre (1-14b) ; journal, événements script_run ; frozen/script.py | 1 |
| session:legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z | maintenue | judged | 2026-11-07 | fragment_overlap jugé vocabulaire de format : les 4 fragments viennent de 3 littéraux de noms de chambre (cass. civ. 1re, 2e, 3e) parmi 57 ; aucun numéro, aucune date, aucune référence d'exemple recopiée | spec 1-14, jugements à rendre (1-14b) ; journal, événements script_run ; frozen/script.py | 1 |

### Retirées des agrégats

- automaton-A-literal-mimo-v2.6-pro-t1-20261105T233158Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- automaton-A-literal-sonnet-5.5-t1-20261106T042957Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- automaton-A-program-mimo-v2.6-pro-t1-20261105T231059Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- automaton-A-program-sonnet-5.5-t1-20261106T042934Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- automaton-B-mimo-v2.6-pro-t1-20261105T233435Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- automaton-B-sonnet-5.5-t1-20261106T043025Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- compare-A-literal-mimo-v2.6-pro-t1-20261105T230436Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- compare-A-literal-sonnet-5.5-t1-20261106T042847Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- compare-A-program-mimo-v2.6-pro-t1-20261105T225332Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- compare-A-program-sonnet-5.5-t1-20261106T042604Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- compare-A-program-sonnet-5.5-t1-20261106T042737Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- compare-B-mimo-v2.6-pro-t1-20261105T231047Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- compare-B-sonnet-5.5-t1-20261106T042926Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- legal_s-A-program-1e4-mimo-v2.6-pro-t1-20261106T174235Z : annexe (MiMo A-programme 10⁴, étape 2 (64000 jetons, effort medium, tronquées ×3) : déjà mis en annexe par 1-10 ; seul l'essai de l'étape 3 (même config, entrée [[session]] ci-dessus) compte)
- legal_s-A-program-1e4-mimo-v2.6-pro-t2-20261106T175503Z : annexe (MiMo A-programme 10⁴, étape 2 (64000 jetons, effort medium, tronquées ×3) : déjà mis en annexe par 1-10 ; seul l'essai de l'étape 3 (même config, entrée [[session]] ci-dessus) compte)
- legal_s-A-program-1e4-mimo-v2.6-pro-t3-20261106T180740Z : annexe (MiMo A-programme 10⁴, étape 2 (64000 jetons, effort medium, tronquées ×3) : déjà mis en annexe par 1-10 ; seul l'essai de l'étape 3 (même config, entrée [[session]] ci-dessus) compte)
- legal_s-B-mimo-v2.6-pro-t1-20261106T060302Z : annexe (MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10 ; B legal_s t3 (3968/4000) cité en annexe du rapport, hors case)
- legal_s-B-mimo-v2.6-pro-t1-20261106T165222Z : annexe (MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : réglage remplacé par l'étape 3, déjà mis en annexe par 1-10)
- legal_s-B-mimo-v2.6-pro-t2-20261106T061711Z : annexe (MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10 ; B legal_s t3 (3968/4000) cité en annexe du rapport, hors case)
- legal_s-B-mimo-v2.6-pro-t2-20261106T170346Z : annexe (MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : réglage remplacé par l'étape 3, déjà mis en annexe par 1-10)
- legal_s-B-mimo-v2.6-pro-t3-20261106T063042Z : annexe (MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10 ; B legal_s t3 (3968/4000) cité en annexe du rapport, hors case)
- legal_s-B-mimo-v2.6-pro-t3-20261106T171527Z : annexe (MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : réglage remplacé par l'étape 3, déjà mis en annexe par 1-10)
- legal_s_reserved-B-mimo-v2.6-pro-t1-20261106T064206Z : annexe (MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10)
- legal_s_reserved-B-mimo-v2.6-pro-t1-20261106T172547Z : annexe (MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : déjà mis en annexe par 1-10 ; B t2 et t3 gelées (89,7 et 90,0 %) citées en annexe du rapport, hors case)
- legal_s_reserved-B-mimo-v2.6-pro-t2-20261106T065445Z : annexe (MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10)
- legal_s_reserved-B-mimo-v2.6-pro-t2-20261106T173223Z : annexe (MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : déjà mis en annexe par 1-10 ; B t2 et t3 gelées (89,7 et 90,0 %) citées en annexe du rapport, hors case)
- legal_s_reserved-B-mimo-v2.6-pro-t3-20261106T070932Z : annexe (MiMo étape 1 (64000 jetons, effort par défaut, graine non transmise) : réglage antérieur à la décision d'Anaël sur l'effort, déjà mis en annexe par 1-10)
- legal_s_reserved-B-mimo-v2.6-pro-t3-20261106T173602Z : annexe (MiMo étape 2 (64000 jetons, effort medium, graine non transmise) : déjà mis en annexe par 1-10 ; B t2 et t3 gelées (89,7 et 90,0 %) citées en annexe du rapport, hors case)
- parity-A-literal-mimo-v2.6-pro-t1-20261105T224942Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- parity-A-literal-sonnet-5.5-t1-20261106T042814Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- parity-A-program-mimo-v2.6-pro-t1-20261105T224224Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- parity-A-program-mimo-v2.6-pro-t1-20261105T224746Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- parity-A-program-sonnet-5.5-t1-20261106T042528Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- parity-B-mimo-v2.6-pro-t1-20261105T225302Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- parity-B-sonnet-5.5-t1-20261106T042840Z : annexe (séances jouet de 1-8 : calibrage du protocole, hors conclusions (methodes-et-lots.md) ; montrées en annexe)
- annexe-fields1/train/legal_s-F-n1024-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n1024-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n1024-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n256-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n256-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n256-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n32768-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n32768-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n32768-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n64-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n64-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n64-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n8192-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n8192-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s-F-n8192-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n1024-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n1024-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n1024-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n256-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n256-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n256-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n32768-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n32768-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n32768-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n64-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n64-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n64-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n8192-s0 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n8192-s1 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))
- annexe-fields1/train/legal_s_reserved-F-n8192-s2 : annexe (F legal.fields@1 (champs scalaires) : annexe de 1-11 ; F retenu = legal.fields@2 (one-hot))

### Non évalués

Aucun.

### Avertissements

Aucun.
