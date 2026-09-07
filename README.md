# UGC Ads Studio

Génère des publicités façon UGC (contenu généré par un créateur) avec un
avatar IA ultra-réaliste qui parle de ton produit : tu décris le produit
(ou écris ton propre script), tu choisis un avatar et une voix, et
l'application génère une vidéo verticale ou horizontale prête à poster,
sous-titres inclus.

## Fonctionnement

1. **Le produit** — nom + description courte, avec un bouton pour générer
   un script publicitaire automatiquement (via l'IA).
2. **Le script** — le texte exact que l'avatar va dire (modifiable).
3. **L'avatar** — choix visuel parmi les avatars disponibles sur ton compte
   HeyGen.
4. **La voix** — choix parmi les voix disponibles.
5. **Format & options** — vertical (TikTok/Reels/Shorts) ou horizontal,
   avec ou sans sous-titres incrustés.

La génération se fait en tâche de fond : avatar (HeyGen) → téléchargement
de la vidéo → incrustation des sous-titres (ffmpeg) → vidéo finale
disponible dans "Mes pubs", avec lecture et téléchargement.

## Prérequis externes

### Compte HeyGen (obligatoire)

L'application utilise [HeyGen](https://www.heygen.com/) pour générer les
avatars IA qui parlent. Sans clé API HeyGen, l'app se lance mais les
sections "avatar" et "voix" affichent une erreur claire et la génération
de pub est désactivée.

1. Crée un compte sur https://app.heygen.com (une offre gratuite avec
   crédits d'essai existe, mais génère peu de vidéos ; un abonnement payant
   est nécessaire pour un usage régulier).
2. Une fois connecté, va dans les paramètres du compte → **API** pour
   récupérer ta clé API (`API Key`).
3. Renseigne-la dans la variable d'environnement `HEYGEN_API_KEY`.

### Clé Anthropic (optionnelle)

Utilisée uniquement pour le bouton "Générer un script avec l'IA". Sans
elle, ce bouton renvoie une erreur mais tu peux toujours écrire ton script
manuellement.

- Variable d'environnement : `ANTHROPIC_API_KEY`

## Lancer en local

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crée un fichier `.env` à la racine du dépôt (à côté de `backend/` et
`frontend/`) :

```
HEYGEN_API_KEY=ta_cle_heygen
ANTHROPIC_API_KEY=ta_cle_anthropic   # optionnel
```

Puis lance le serveur (depuis `backend/`) :

```bash
uvicorn app.main:app --reload --port 8000
```

Ouvre http://localhost:8000 dans ton navigateur.

`ffmpeg` doit être installé sur la machine (utilisé pour incruster les
sous-titres).

## Déployer sur Render (accès mobile, sans ordinateur)

Ce dépôt contient un `Dockerfile` et un `render.yaml` prêts à l'emploi.

1. Pousse ce dépôt (ou cette branche) sur GitHub.
2. Sur [render.com](https://render.com), crée un compte, puis **New +** →
   **Blueprint**, et sélectionne ce dépôt. Render détecte `render.yaml`
   automatiquement.
3. Renseigne les variables d'environnement demandées (`HEYGEN_API_KEY`,
   `ANTHROPIC_API_KEY`) dans l'onglet **Environment** du service.
4. Déploie. Une fois en ligne, l'URL Render fonctionne depuis un téléphone,
   sans avoir besoin d'un ordinateur allumé.

### Limites de l'offre gratuite Render à connaître

- **Stockage éphémère** : les vidéos générées sont perdues si le service
  redémarre ou se met en veille. Télécharge tes vidéos importantes.
- **Mise en veille après inactivité** : le premier chargement après une
  pause peut prendre 30 à 60 secondes.
- **CPU/RAM partagés** : l'incrustation des sous-titres (ffmpeg) peut être
  plus lente que sur une machine locale.
- La génération d'avatar elle-même se fait côté HeyGen (pas de charge
  supplémentaire sur Render), seule l'incrustation des sous-titres tourne
  localement.

## Notes techniques

- Les sous-titres ne dépendent pas de l'API HeyGen : ils sont générés en
  interne à partir du texte du script et de la durée réelle de la vidéo
  (découpage proportionnel en mots), puis incrustés avec ffmpeg — plus
  fiable que d'attendre un format de sous-titres externe.
- Le statut d'une pub évolue ainsi : `pending` → `generating` →
  `downloading` → `captioning` (si sous-titres activés) → `done`, ou
  `error` avec un message explicite en cas d'échec à une étape.
