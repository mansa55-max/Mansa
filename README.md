# Mansa

Application locale pour importer un film — en le recherchant par titre ou en
important un fichier vidéo — et en obtenir automatiquement un résumé.

## Fonctionnalités

- **Recherche par titre** : cherche un film via [TMDB](https://www.themoviedb.org/)
  et importe ses infos (affiche, genres, synopsis officiel).
- **Import d'un fichier vidéo** (.mp4, .mkv, .mov, .avi, .webm, .m4v) : l'audio
  est extrait (ffmpeg), transcrit localement (faster-whisper), puis résumé.
- **Résumé** : généré par IA (Claude, via `ANTHROPIC_API_KEY`) si une clé est
  configurée, sinon un résumé automatique extractif 100% local est utilisé —
  l'appli fonctionne donc sans aucune clé API pour la partie vidéo.
- **Vidéo résumé (TikTok / YouTube)** : pour un film importé par fichier vidéo,
  génère automatiquement une vidéo courte à partir d'extraits de la vidéo
  source, avec narration audio du résumé (synthèse vocale) et sous-titres
  incrustés, exportée en vertical 9:16 (TikTok / Shorts) et/ou horizontal 16:9
  (YouTube). ⚠️ Republier des extraits d'un film dont tu n'as pas les droits
  enfreint généralement le droit d'auteur (Content ID, retraits DMCA, strikes) —
  utilise cette fonctionnalité uniquement sur du contenu dont tu as les droits
  ou l'autorisation.
- Historique des films importés avec suivi de la progression (extraction →
  transcription → résumé) et suppression.

## Prérequis

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/download.html) installé et disponible dans le
  `PATH` (nécessaire pour l'import de fichiers vidéo et la génération de
  vidéos résumé) :
  - Debian/Ubuntu : `sudo apt install ffmpeg`
  - macOS : `brew install ffmpeg`
- (Optionnel, secours hors-ligne pour la narration) `espeak-ng` : utilisé
  automatiquement si `edge-tts` échoue (pas de connexion internet). Sans
  connexion internet ni `espeak-ng`, la génération de vidéo résumé échouera
  avec un message explicite.
  - Debian/Ubuntu : `sudo apt install espeak-ng`

## Installation

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copie `.env.example` vers `.env` à la racine du projet et renseigne les clés
souhaitées :

```bash
cp .env.example .env
```

- `TMDB_API_KEY` : nécessaire pour la recherche de films (clé gratuite sur
  https://www.themoviedb.org/settings/api). Sans cette clé, seul l'import par
  fichier vidéo fonctionne.
- `ANTHROPIC_API_KEY` : optionnelle, améliore la qualité des résumés. Sans
  elle, un résumé extractif local est généré à la place.
- `TTS_VOICE` : voix de narration edge-tts pour les vidéos résumé (défaut
  `fr-FR-DeniseNeural`). Liste des voix : `edge-tts --list-voices`.

## Lancer l'application

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Puis ouvre http://127.0.0.1:8000 dans ton navigateur.

Le premier import vidéo télécharge le modèle Whisper choisi (par défaut
`small`, ~500 Mo) — cela peut prendre un moment la première fois.

## Déploiement en ligne (accès depuis un téléphone, sans ordinateur)

L'appli est conçue pour un usage local, mais peut être déployée sur
[Render](https://render.com) (offre gratuite) pour y accéder depuis un
téléphone via un simple lien.

⚠️ Limites du tier gratuit Render à connaître avant de déployer :
- **Stockage éphémère** : les vidéos importées/générées sont perdues à
  chaque redéploiement ou redémarrage du service (pas de disque persistant
  sur l'offre gratuite).
- **CPU partagé limité** : la transcription et le montage vidéo peuvent
  prendre plusieurs minutes.
- **Mise en veille** : le service s'endort après une période d'inactivité et
  met du temps à redémarrer au premier accès suivant.

### Étapes

1. Crée un compte gratuit sur https://render.com (connexion possible avec
   GitHub).
2. Sur le tableau de bord Render : **New → Blueprint**, puis sélectionne ce
   dépôt GitHub (`mansa55-max/Mansa`, branche `claude/film-summary-generator-dm8u8r`
   ou `main` une fois la PR fusionnée). Render détecte automatiquement le
   fichier `render.yaml` à la racine et configure le service (basé sur le
   `Dockerfile`, qui installe ffmpeg + espeak-ng).
3. Render demandera de renseigner `TMDB_API_KEY` et `ANTHROPIC_API_KEY`
   (cette dernière optionnelle) — à saisir dans les champs proposés.
4. Clique sur **Apply**. Le premier déploiement prend quelques minutes
   (construction de l'image + téléchargement du modèle Whisper au premier
   import).
5. Une fois déployé, Render fournit une URL du type
   `https://mansa-xxxx.onrender.com` — ouvre-la depuis ton téléphone.

Le modèle Whisper est réglé sur `tiny` par défaut pour ce déploiement
(`WHISPER_MODEL_SIZE` dans `render.yaml`) afin de rester dans les limites de
RAM du tier gratuit (512 Mo) ; la qualité de transcription est un peu moins
bonne qu'avec `small` en local.

## Structure

```
backend/app/
  main.py            # point d'entrée FastAPI + sert le frontend
  config.py           # variables d'environnement, chemins
  models.py, schemas.py
  services/
    tmdb.py            # recherche / détails via TMDB
    transcription.py    # ffmpeg + faster-whisper
    summarizer.py        # résumé IA (optionnel) ou extractif local
    tts.py                # narration audio + sous-titres (edge-tts ou espeak-ng)
    recap.py               # montage ffmpeg de la vidéo résumé (9:16 / 16:9)
  routers/
    search.py, movies.py, import_video.py, recap.py
frontend/               # page unique HTML/CSS/JS (sans framework)
data/                    # base SQLite + fichiers vidéo/audio/recaps (ignoré par git)
```
