# Déployer l'application dans Home Assistant

Ce dossier (`cave_a_vin_addon/`) est un add-on Home Assistant complet :
backend FastAPI + interface web + OCR + enrichissement IA, packagé avec
Dockerfile et config.yaml. Ce guide explique comment l'installer sur le
Raspberry Pi et y charger tes données déjà migrées de PLOC.

Je n'ai pas pu tester le démarrage réel du serveur dans cet environnement
(pas d'accès réseau pour installer FastAPI ici) : j'ai validé toute la
logique métier (création de cave, calcul de stock, jointures, etc.)
directement contre le schéma SQL, avec succès. Le code lui-même est du
FastAPI standard — mais teste-le en conditions réelles sur le Pi et
reviens vers moi si quelque chose coince au démarrage.

## 1. Copier l'add-on sur le Pi

Home Assistant OS cherche les add-ons locaux dans le dossier `/addons`
de la machine qui héberge HA. Le plus simple pour y accéder :

1. Installe l'add-on officiel **"Samba share"** ou **"Studio Code Server"**
   depuis Paramètres → Add-ons → Boutique d'add-ons (si ce n'est pas déjà fait).
2. Connecte-toi au partage réseau du Pi (ou ouvre le terminal de Studio Code
   Server) et crée le dossier `/addons/cave_a_vin/`.
3. Copie-y tout le contenu de ce dossier `cave_a_vin_addon/` (config.yaml,
   Dockerfile, run.sh, requirements.txt, le dossier `app/`).

## 2. Installer et démarrer l'add-on

1. Dans Home Assistant : Paramètres → Add-ons → Boutique d'add-ons → icône
   ⋮ en haut à droite → **"Actualiser"**. L'add-on apparaît dans la section
   **"Add-ons locaux"** sous le nom "Cave à vin partagée".
2. Clique dessus, puis **Installer** (la première construction de l'image
   Docker prend quelques minutes sur un Raspberry Pi, le temps d'installer
   tesseract-ocr et les dépendances Python).
3. Va dans l'onglet **Configuration** de l'add-on et colle ta clé API
   Anthropic dans le champ `anthropic_api_key` (récupérable sur
   console.anthropic.com) — nécessaire pour le bouton "Enrichir avec l'IA".
   Tu peux laisser vide pour l'instant et l'ajouter plus tard.
4. Démarre l'add-on. Comme `ingress: true` est activé, une icône "Cave à
   vin" apparaît directement dans le menu latéral de Home Assistant.

## 3. Charger tes données déjà migrées (au lieu de partir d'une base vide)

Au premier démarrage, l'add-on crée une base vide dans son volume
persistant `/data`. Pour repartir directement avec tes 86 vins migrés
de PLOC plutôt que de recommencer à zéro :

1. Arrête l'add-on (bouton "Stop" dans son onglet Info).
2. Repère le dossier de données de l'add-on sur le Pi : via Samba/Studio
   Code Server, cherche `/addon_configs/local_cave_a_vin/` ou
   `/data/` selon la version du superviseur (le chemin exact est indiqué
   dans l'onglet "Info" de l'add-on, section "Emplacement des données").
3. Copie-y le fichier `cave_a_vin.sqlite` et le dossier `photos/` fournis
   dans `nouvelle_base/` (résultat de la migration PLOC), en écrasant la
   base vide.
4. Redémarre l'add-on. Tes vins, caves et mouvements de stock existants
   apparaissent immédiatement dans l'interface.

## 4. Utilisation depuis iPhone et PC

- **iPhone** : ouvre l'app Home Assistant (ou Safari), l'icône "Cave à
  vin" est dans le menu latéral comme n'importe quelle autre intégration.
  L'authentification est celle déjà utilisée pour se connecter à HA — pas
  de mot de passe supplémentaire à gérer.
- **PC** : même chose depuis un navigateur, à l'adresse de ton instance HA.
- Chaque habitant peut se choisir dans le sélecteur en haut de l'app (créé
  automatiquement au premier lancement avec un compte "Admin" — ajoute les
  autres habitants via le bouton correspondant, ou directement en base).

## 5. Limites connues de cette v1

- Pas de redimensionnement "intelligent" de cave si tu réduis les
  lignes/colonnes après coup (les cases en trop ne sont pas supprimées
  automatiquement si elles contiennent déjà une bouteille).
- L'enrichissement IA part du nom saisi + texte OCR : la qualité dépend
  fortement de la netteté de la photo et de la police de l'étiquette.
- Pas encore de carte visuelle de la cave, de gestion de repas/événements,
  ni de gabarits de dégustation avancés (cf. `conception_base_de_donnees.md`).

## 6. Prochaines pistes

- Ajouter une vraie recherche/filtre par appellation, région, couleur.
- Exporter/sauvegarder automatiquement `cave_a_vin.sqlite` (ex. vers Google
  Drive ou un autre stockage) en plus de la sauvegarde HA classique.
- Notifications HA (ex. "il ne reste que 2 bouteilles de tel vin") en
  s'appuyant sur l'automatisation native de Home Assistant, qui peut
  interroger l'API de l'add-on.
