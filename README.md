# wine_cellar

Repository d'add-on Home Assistant pour **Cave à vin partagée**.

## Installation dans Home Assistant

1. Ouvrir **Settings → Add-ons → Add-on Store**.
2. Cliquer sur le menu (⋮) en haut à droite, puis **Repositories**.
3. Ajouter :
   `https://github.com/niforget/wine_cellar`
4. Actualiser la boutique d'add-ons.
5. Installer l'add-on **Cave à vin partagée**.

## Configuration

Option disponible :

- `anthropic_api_key` (optionnelle) : clé API Anthropic pour l'enrichissement IA des fiches vin.

## Structure du repository

Ce repository suit la structure officielle Home Assistant avec un sous-dossier d'add-on :

```text
wine_cellar/
├── README.md
├── GUIDE_DEPLOIEMENT.md
└── cave_a_vin/
    ├── config.yaml
    ├── Dockerfile
    ├── manifest.json
    ├── requirements.txt
    ├── run.sh
    └── app/
```