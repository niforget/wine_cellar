# Cave à vin partagée — Add-on Home Assistant

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/niforget/wine_cellar)
[![HA Addon](https://img.shields.io/badge/Home%20Assistant-Add--on-brightgreen)](https://www.home-assistant.io/addons/)

Gérez votre cave à vin directement depuis Home Assistant : fiches de vin, suivi du stock, OCR d'étiquette et enrichissement automatique par IA (Claude / Anthropic). Accessible depuis votre iPhone, tablette ou PC via l'ingress natif de Home Assistant — sans mot de passe supplémentaire.

---

## Fonctionnalités

- **Multi-caves** : créez autant de caves que vous voulez avec grille de rangement personnalisée.
- **Fiches de vin** complètes : appellation, millésime, producteur, couleur, degré, composition, commentaires de dégustation…
- **OCR d'étiquette** : photographiez une étiquette, le texte est extrait automatiquement (Tesseract).
- **Enrichissement IA** : un clic sur "Enrichir avec l'IA" complète automatiquement la fiche via Claude (Anthropic).
- **Gestion du stock** : entrées/sorties de bouteilles avec historique.
- **Multi-utilisateurs** : chaque habitant choisit son profil dans le sélecteur en haut de l'interface.
- **Ingress HA** : s'intègre dans le menu latéral de Home Assistant comme une vraie intégration.

---

## Prérequis

- **Home Assistant OS** ou **Home Assistant Supervised** (superviseur HA requis pour les add-ons).
- Optionnel : une clé API **Anthropic** pour la fonctionnalité d'enrichissement IA (gratuite jusqu'à un certain volume sur [console.anthropic.com](https://console.anthropic.com)).

---

## Installation via dépôt personnalisé HA

### 1. Ajouter ce dépôt comme source d'add-ons

1. Dans Home Assistant : **Paramètres → Add-ons → Boutique d'add-ons**.
2. Cliquez sur l'icône **⋮** (trois points) en haut à droite, puis **"Dépôts"**.
3. Collez l'URL du dépôt :
   ```
   https://github.com/niforget/wine_cellar
   ```
4. Cliquez **Ajouter**, puis **Fermer**.
5. Actualisez la page (icône ⋮ → **"Actualiser"**) — l'add-on **"Cave à vin partagée"** apparaît dans la liste.

### 2. Installer et démarrer l'add-on

1. Cliquez sur l'add-on **"Cave à vin partagée"** et cliquez **Installer**.  
   > La première installation prend quelques minutes (compilation de l'image Docker avec Tesseract-OCR et les dépendances Python).
2. Rendez-vous sur l'onglet **Configuration** et renseignez votre clé API Anthropic dans le champ `anthropic_api_key` (voir section suivante). Ce champ est optionnel : laissez-le vide si vous n'utilisez pas l'enrichissement IA.
3. Cliquez **Démarrer**.

Une icône **"Cave à vin"** (🍷) apparaît directement dans le menu latéral de Home Assistant.

---

## Configuration de la clé API Anthropic

La clé est nécessaire uniquement pour le bouton **"Enrichir avec l'IA"** qui complète automatiquement les fiches de vin.

1. Créez un compte sur [console.anthropic.com](https://console.anthropic.com) et générez une clé API.
2. Dans HA : **Paramètres → Add-ons → Cave à vin partagée → Configuration**.
3. Collez la clé dans le champ **`anthropic_api_key`** et cliquez **Enregistrer**.
4. Redémarrez l'add-on pour prise en compte.

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| `anthropic_api_key` | Texte (optionnel) | *(vide)* | Clé API Anthropic pour l'enrichissement IA |

---

## Utilisation de base

### Première connexion

Au premier démarrage, un utilisateur **Admin** est créé automatiquement. Sélectionnez-le dans le menu déroulant en haut de l'interface. Ajoutez d'autres habitants via le bouton **"Ajouter un utilisateur"**.

### Créer une cave

1. Cliquez sur **"Nouvelle cave"**.
2. Donnez-lui un nom et définissez le nombre de lignes × colonnes de la grille.
3. Validez : la grille de rangements apparaît.

### Ajouter un vin

1. Dans une cave, cliquez sur un emplacement vide ou sur **"Nouveau vin"**.
2. Remplissez le nom du vin (les autres champs sont optionnels).
3. **Optionnel — OCR** : uploadez une photo de l'étiquette → le texte est extrait automatiquement.
4. **Optionnel — Enrichissement IA** : cliquez **"Enrichir avec l'IA"** → la fiche est complétée (appellation, millésime, producteur, etc.).
5. Enregistrez.

### Suivre le stock

Chaque vin dispose d'un compteur de bouteilles. Les mouvements (entrées/sorties) sont enregistrés avec la date et l'utilisateur.

---

## Limitations connues (v0.1.0)

- La réduction de la grille d'une cave (moins de lignes/colonnes) ne supprime pas automatiquement les emplacements occupés.
- La qualité de l'enrichissement IA dépend de la netteté de la photo et de la lisibilité de l'étiquette.
- Pas encore de carte visuelle de cave, de gestion d'événements/repas, ni de gabarits de dégustation avancés.
- L'ingress HA délègue l'authentification à Home Assistant : pas de gestion de permissions fine entre utilisateurs de l'add-on.

---

## Sauvegarde des données

Les données (base SQLite + photos) sont stockées dans le volume persistant `/data` de l'add-on et sont **incluses dans les sauvegardes natives de Home Assistant** (Paramètres → Système → Sauvegardes).

---

## Support et signalement de bugs

Ouvrez une issue sur [github.com/niforget/wine_cellar/issues](https://github.com/niforget/wine_cellar/issues) en précisant :

- La version de Home Assistant et du superviseur.
- Les logs de l'add-on (onglet **Journal** dans l'interface de l'add-on).
- Les étapes pour reproduire le problème.

---

## Pistes d'évolution

- Recherche et filtres avancés (appellation, région, couleur, millésime…).
- Export/sauvegarde automatique de la base vers un stockage externe.
- Notifications HA ("Il ne reste que 2 bouteilles de [vin]") via les automatisations natives.
- Carte visuelle interactive de la cave.

---

## Licence

Ce projet est distribué librement. Voir le dépôt pour les détails.