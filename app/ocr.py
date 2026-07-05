"""
OCR d'une photo d'etiquette via le binaire tesseract (installe dans
l'image Docker de l'add-on, voir Dockerfile). Pas de dependance Python
supplementaire : on appelle simplement la commande en ligne.
"""
import subprocess
import tempfile
import os


def extraire_texte(chemin_image: str, langues: str = "fra+eng") -> str:
    """Retourne le texte brut detecte sur l'image. Chaine vide si echec."""
    try:
        with tempfile.NamedTemporaryFile(suffix="") as tmp_out:
            base = tmp_out.name
        result = subprocess.run(
            ["tesseract", chemin_image, base, "-l", langues],
            capture_output=True,
            timeout=30,
        )
        txt_path = base + ".txt"
        if result.returncode == 0 and os.path.exists(txt_path):
            with open(txt_path, encoding="utf-8", errors="ignore") as f:
                texte = f.read()
            os.remove(txt_path)
            return texte.strip()
    except Exception as e:
        print(f"[ocr] erreur : {e}")
    return ""
