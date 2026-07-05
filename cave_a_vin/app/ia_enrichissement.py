"""
Enrichissement d'une fiche de vin par IA (API Claude / Anthropic).

La cle d'API est fournie via la variable d'environnement ANTHROPIC_API_KEY,
elle-meme alimentee par l'option "anthropic_api_key" du config.yaml de
l'add-on (renseignee par l'utilisateur dans l'onglet Configuration de HA).
Si la cle n'est pas configuree, la fonction renvoie une erreur explicite
plutot que de planter l'application.
"""
import os
import json
import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODELE_PAR_DEFAUT = "claude-sonnet-4-5"

CHAMPS_ATTENDUS = [
    "nom", "cuvee", "millesime", "producteur", "appellation", "region",
    "pays", "couleur", "composition", "degre_alcool", "commentaires",
]


def enrichir_fiche(nom_vin: str, texte_ocr: str, modele: str = MODELE_PAR_DEFAUT) -> dict:
    """
    Appelle Claude pour proposer des valeurs structurees a partir du nom
    du vin et/ou du texte OCR de l'etiquette. Retourne un dict :
        {"ok": True, "champs": {...}, "modele": "..."}
    ou
        {"ok": False, "erreur": "..."}
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return {"ok": False, "erreur": "Aucune cle API Anthropic configuree (option anthropic_api_key)."}

    prompt = f"""Tu recois le nom d'un vin et/ou le texte OCR (souvent imparfait) lu sur son etiquette.
Nom saisi : {nom_vin or "(inconnu)"}
Texte OCR de l'etiquette :
---
{texte_ocr or "(aucun)"}
---

Propose les champs suivants pour la fiche de ce vin, au mieux de ce que tu peux deduire.
Reponds UNIQUEMENT avec un objet JSON valide, sans texte autour, avec exactement ces cles
(laisse une chaine vide "" ou null si tu ne sais pas) :
{{"nom": "", "cuvee": "", "millesime": null, "producteur": "", "appellation": "",
"region": "", "pays": "", "couleur": "", "composition": "", "degre_alcool": null,
"commentaires": "une courte description du vin, 2-3 phrases"}}"""

    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": modele,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        texte_reponse = "".join(
            bloc.get("text", "") for bloc in data.get("content", []) if bloc.get("type") == "text"
        )
        champs = json.loads(texte_reponse)
        return {"ok": True, "champs": champs, "modele": modele}
    except requests.exceptions.RequestException:
        return {"ok": False, "erreur": "Erreur reseau/API lors de l'enrichissement IA."}
    except (json.JSONDecodeError, ValueError):
        return {"ok": False, "erreur": "Reponse IA non exploitable."}
