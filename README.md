# 🎮 GameCatalogue

GameCatalogue est une application web permettant de découvrir, rechercher et recommander des jeux vidéo.

L'application permet notamment de :

* rechercher des jeux vidéo ;
* parcourir un catalogue de jeux ;
* filtrer et trier les résultats ;
* consulter la fiche détaillée d'un jeu ;
* visualiser les screenshots ;
* regarder le trailer YouTube d'un jeu ;
* ajouter et retirer des jeux des favoris ;
* conserver les favoris sur le serveur dans un fichier JSON ;
* utiliser un assistant IA nommé **GameBot** pour rechercher des jeux en langage naturel.

Exemple de demande adressée à GameBot :

> Je cherche un RPG solo sur PC avec une grosse histoire et une bonne note.

GameBot transforme cette demande en critères structurés grâce à **Mistral AI**, puis utilise ces critères pour rechercher les jeux correspondants dans **RAWG**.

---

# 1. Technologies utilisées

## Backend

* Python 3
* Flask
* Requests
* python-dotenv
* Mistral AI SDK

## Frontend

* HTML5
* CSS3
* JavaScript vanilla

Aucun framework frontend comme React, Vue ou Angular n'est utilisé.

## APIs

### RAWG Video Games Database

RAWG est utilisé comme source principale pour les informations relatives aux jeux :

* noms ;
* images ;
* notes ;
* dates de sortie ;
* genres ;
* plateformes ;
* développeurs ;
* éditeurs ;
* screenshots.

### YouTube Data API v3

L'API YouTube est utilisée pour rechercher les trailers des jeux.

### Mistral AI

Mistral est utilisé par GameBot pour comprendre les demandes écrites en langage naturel et les transformer en critères de recherche exploitables par RAWG.

Le modèle actuellement utilisé est :

```text
ministral-3b-latest
```

---

# 2. Architecture du projet

```text
GameCatalogue/
│
├── app.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── data/
│   └── favorites.json
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── script.js
│
└── utils/
    ├── __init__.py
    ├── rawg.py
    ├── youtube.py
    └── mistral.py
```

## Rôle des différents fichiers

### `app.py`

Contient le serveur Flask et les routes de l'application.

Il gère notamment :

* les routes RAWG ;
* la route YouTube ;
* la route GameBot ;
* les endpoints des favoris ;
* les erreurs HTTP ;
* le lancement du serveur.

### `utils/rawg.py`

Contient la communication avec l'API RAWG.

### `utils/youtube.py`

Contient la communication avec l'API YouTube.

### `utils/mistral.py`

Contient la communication avec Mistral AI et la transformation des demandes utilisateur en critères structurés.

### `templates/index.html`

Contient la structure HTML de l'application.

### `static/css/style.css`

Contient l'ensemble du design de l'application.

### `static/js/script.js`

Gère les interactions côté navigateur :

* recherche ;
* filtres ;
* pagination ;
* cartes de jeux ;
* modale ;
* favoris ;
* GameBot ;
* thème clair/sombre ;
* menu mobile.

### `data/favorites.json`

Contient les jeux ajoutés aux favoris.

---

# 3. Installation de Python

Le projet nécessite Python 3.

Pour vérifier que Python est installé :

```powershell
python --version
```

ou :

```powershell
py --version
```

---

# 4. Création de l'environnement virtuel

Depuis le dossier du projet :

```powershell
python -m venv venv
```

L'environnement virtuel est appelé :

```text
venv
```

---

# 5. Activation de l'environnement virtuel

Sous Windows PowerShell :

```powershell
.\venv\Scripts\activate
```

Sous Linux/macOS :

```bash
source venv/bin/activate
```

Si l'activation PowerShell est bloquée, il est également possible d'utiliser directement Python depuis le dossier `venv` :

```powershell
.\venv\Scripts\python.exe app.py
```

---

# 6. Installation des dépendances

Installer les dépendances avec :

```powershell
python -m pip install -r requirements.txt
```

Les principales dépendances sont :

* Flask ;
* Requests ;
* python-dotenv ;
* Mistral AI.

---

# 7. Configuration du fichier `.env`

Créer un fichier `.env` à la racine du projet.

Exemple :

```env
RAWG_API_KEY=Votre_cle_RAWG
YOUTUBE_API_KEY=Votre_cle_YOUTUBE
MISTRAL_API_KEY=Votre_cle_MISTRAL
MISTRAL_MODEL=ministral-3b-latest
PORT=5000
```

Les vraies clés API doivent uniquement être placées dans `.env`.

Elles ne doivent jamais être écrites dans :

* `script.js` ;
* `index.html` ;
* le CSS ;
* le dépôt Git ;
* les réponses envoyées au navigateur.

---

# 8. Obtenir les clés API

## RAWG

Créer un compte sur RAWG et obtenir une clé API.

La clé est ensuite placée dans :

```env
RAWG_API_KEY=...
```

## YouTube

Créer un projet Google Cloud et activer :

```text
YouTube Data API v3
```

La clé est ensuite placée dans :

```env
YOUTUBE_API_KEY=...
```

## Mistral

Créer une clé API depuis Mistral AI.

La clé est placée dans :

```env
MISTRAL_API_KEY=...
```

Le modèle actuellement utilisé par le projet est :

```env
MISTRAL_MODEL=ministral-3b-latest
```

---

# 9. Lancer l'application

Depuis le dossier du projet :

```powershell
python app.py
```

Ou, avec le Python du venv :

```powershell
.\venv\Scripts\python.exe app.py
```

Le serveur démarre normalement sur :

```text
http://127.0.0.1:5000
```

Ouvrir ensuite cette adresse dans un navigateur.

---

# 10. Fonctionnement de RAWG

Le backend communique avec RAWG grâce aux routes Flask.

## Catalogue

```http
GET /api/games
```

Exemple :

```text
/api/games?search=minecraft
```

La recherche peut utiliser notamment :

* recherche par nom ;
* genre ;
* plateforme ;
* tri ;
* date ;
* pagination.

## Détails d'un jeu

```http
GET /api/games/<id>
```

Exemple :

```text
/api/games/536886
```

## Screenshots

```http
GET /api/games/<id>/screenshots
```

Les données retournées par RAWG sont utilisées directement dans l'application.

Aucune information fictive n'est créée.

---

# 11. Fonctionnement de YouTube

Route :

```http
GET /api/trailer?game=NomDuJeu
```

L'application recherche un trailer correspondant au jeu.

Lorsqu'un résultat est disponible, la fiche peut afficher :

* le titre ;
* la chaîne ;
* la vidéo intégrée ;
* le lien YouTube.

Les vidéos ne sont pas téléchargées par l'application.

---

# 12. Fonctionnement de GameBot

GameBot utilise Mistral AI pour interpréter une demande écrite en langage naturel.

Route :

```http
POST /api/recommend
```

Exemple :

```json
{
  "message": "Je cherche un RPG solo sur PC avec une grosse histoire."
}
```

Mistral transforme cette demande en critères structurés.

Exemple de structure utilisée :

```json
{
  "search": "",
  "genres": [],
  "platforms": [],
  "tags": [],
  "ordering": "-rating",
  "released_after": "",
  "released_before": ""
}
```

Les critères sont ensuite utilisés côté serveur pour effectuer une recherche dans RAWG.

Le navigateur ne communique jamais directement avec Mistral avec la clé API.

---

# 13. Système de favoris

Les favoris sont stockés **côté serveur**, dans :

```text
data/favorites.json
```

Contrairement à une simple sauvegarde dans le navigateur, les favoris sont maintenant gérés par Flask.

## Récupérer les favoris

```http
GET /api/favorites
```

## Ajouter un favori

```http
POST /api/favorites
```

Exemple de données envoyées :

```json
{
  "id": 536886,
  "name": "The Binding of Isaac: Repentance",
  "slug": "the-binding-of-isaac-repentance",
  "image": "https://...",
  "rating": 4.5,
  "released": "2021-03-31",
  "genres": [
    {
      "name": "Action"
    }
  ]
}
```

## Supprimer un favori

```http
DELETE /api/favorites/<id>
```

Exemple :

```text
DELETE /api/favorites/536886
```

## Supprimer tous les favoris

```http
DELETE /api/favorites
```

Les informations sont enregistrées dans le fichier :

```json
{
  "favorites": []
}
```

ou, lorsqu'un jeu est ajouté :

```json
{
  "favorites": [
    {
      "id": 536886,
      "name": "The Binding of Isaac: Repentance",
      "slug": "the-binding-of-isaac-repentance",
      "image": "https://...",
      "background_image": "https://...",
      "rating": 4.5,
      "released": "2021-03-31",
      "genres": [
        {
          "name": "Action"
        }
      ]
    }
  ]
}
```

---

# 14. Pourquoi utiliser un fichier JSON pour les favoris ?

Le fichier JSON permet de mettre en place un stockage simple côté serveur sans ajouter de base de données à ce projet.

Avantages dans le contexte du projet :

* facile à comprendre ;
* facile à consulter ;
* facile à modifier ;
* aucune installation de base de données nécessaire ;
* intégration simple avec Flask.

Cette approche est adaptée à un projet scolaire et à une application utilisée localement.

Pour une application multi-utilisateur en production, une véritable base de données serait plus adaptée.

---

# 15. Fonctionnalités de l'interface

## Recherche

La page permet de rechercher des jeux directement depuis :

* la barre de recherche principale ;
* la recherche du catalogue.

## Filtres

L'utilisateur peut filtrer les résultats selon les paramètres disponibles.

## Tri

Plusieurs modes de tri sont disponibles, notamment :

* meilleure note ;
* date de sortie ;
* ordre alphabétique ;
* Metacritic.

## Pagination

Les résultats sont chargés progressivement avec le bouton de chargement supplémentaire.

## Fiche détaillée

La modale d'un jeu affiche notamment :

* image ;
* nom ;
* note ;
* date de sortie ;
* Metacritic ;
* description ;
* genres ;
* plateformes ;
* développeurs ;
* éditeurs ;
* screenshots ;
* trailer ;
* site officiel lorsqu'il est disponible.

## Favoris

Chaque carte possède un bouton :

```text
♡
```

ou :

```text
♥
```

Le jeu peut être ajouté ou retiré des favoris directement depuis la carte.

## GameBot

L'utilisateur peut écrire une demande en langage naturel afin d'obtenir des recommandations correspondant aux critères demandés.

## Mode clair/sombre

Le site possède également un système de thème clair/sombre.

La préférence de thème est sauvegardée dans `localStorage`.

---

# 16. Gestion des erreurs

L'application vérifie notamment :

* les paramètres reçus par Flask ;
* les identifiants de jeux ;
* les paramètres de pagination ;
* les données JSON reçues ;
* la présence des clés API ;
* les réponses des APIs externes.

Les erreurs API sont renvoyées sous forme de JSON pour permettre au frontend de les afficher correctement.

Exemple :

```json
{
  "error": "Message d'erreur"
}
```

---

# 17. Sécurité

Les clés API sont uniquement utilisées côté serveur.

Le fichier `.env` doit être ignoré par Git.

Le fichier `.gitignore` doit notamment contenir :

```text
.env
venv/
.venv/
__pycache__/
*.pyc
.DS_Store
```

Il ne faut jamais publier une clé API dans un fichier frontend.

Il faut également éviter d'exécuter des données utilisateur comme du code.

---

# 18. Tests réalisés

## RAWG

Les fonctionnalités suivantes doivent être vérifiées :

* recherche ;
* catalogue ;
* filtres ;
* tri ;
* pagination ;
* détails ;
* screenshots.

## YouTube

Vérifier :

* recherche du trailer ;
* affichage de la vidéo ;
* gestion d'une absence de résultat.

## Mistral

Exemples de demandes :

```text
Je veux un RPG solo avec une grosse histoire.
```

```text
Je cherche un jeu de course sur PC.
```

```text
Je veux un jeu d'action récent.
```

Vérifier que :

1. Mistral comprend la demande ;
2. les critères sont affichés ;
3. les critères sont réellement utilisés pour rechercher les jeux dans RAWG.

## Favoris

Vérifier :

* ajout d'un favori ;
* affichage du favori ;
* suppression ;
* rechargement de la page ;
* conservation des données dans `data/favorites.json`.

## Frontend

Tester également :

* ordinateur ;
* tablette ;
* mobile ;
* recherche ;
* filtres ;
* modale ;
* GameBot ;
* thème clair/sombre ;
* gestion des erreurs.

---

# 19. Lancement rapide

Une fois Python et les clés API configurés :

```powershell
python -m venv venv
```

Puis :

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Puis :

```powershell
.\venv\Scripts\python.exe app.py
```

Enfin ouvrir :

```text
http://127.0.0.1:5000
```

---

# 20. Résumé du projet

GameCatalogue est une application web full-stack développée avec :

```text
Python
Flask
HTML
CSS
JavaScript vanilla
RAWG API
YouTube Data API
Mistral AI
JSON
```

L'architecture sépare clairement :

```text
Frontend
    ↓
Flask
    ↓
APIs externes
```

Les favoris suivent désormais cette architecture :

```text
Frontend
    ↓
Flask /api/favorites
    ↓
data/favorites.json
```

GameBot suit :

```text
Utilisateur
    ↓
Frontend
    ↓
Flask /api/recommend
    ↓
Mistral AI
    ↓
Critères structurés
    ↓
RAWG
    ↓
Résultats
```

L'application est conçue pour rester simple, compréhensible et présentable dans le cadre d'un projet scolaire.
