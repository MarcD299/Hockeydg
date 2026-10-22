# HockeyDG — Dossier de déploiement Cloudflare Pages

Préparé le 2026-10-15. Site statique prêt à déployer. **Rien n'a été publié en ligne.**

## Contenu

| Fichier | Description |
|---|---|
| `index.html` | Page principale du site (copie du 15 oct. 2026) + bandeau témoins + liens légaux au pied de page |
| `assets/` | Tous les visuels, logos, données JS (~155 Mo) — chemins relatifs, aucun changement requis |
| `confidentialite.html` | Politique de confidentialité FR + EN (convertie de `hockeydg-legal/politique-confidentialite-FR-EN.md`) |
| `conditions.html` | Conditions d'utilisation FR + EN (convertie de `hockeydg-legal/conditions-utilisation-FR-EN.md`) |
| `mentions-legales.html` | Mentions légales FR + EN (source FR : `hockeydg-legal/mentions-legales.md` ; version EN = traduction fidèle, le .md source n'existe qu'en FR) |
| `build-legal.py` | Script de génération des 3 pages légales (relançable si les .md changent) |

## Ce qui a été ajouté au site

1. **Bandeau de consentement témoins** (Loi 25 Québec) : discret en bas de page, boutons Accepter/Refuser,
   choix mémorisé en `localStorage` (`hdg-cookie-consent`), bilingue FR/EN. Réouvrable via le lien
   « Témoins / Cookies » du pied de page.
2. **Liens légaux au pied de page** : Confidentialité · Conditions d'utilisation · Mentions légales
   (+ lien Témoins/Cookies). La langue courante (`?lang=`) est propagée aux pages légales.
3. **Pages légales** : même identité visuelle (variables CSS du site, en-tête avec logo, carte blanche
   coins arrondis, pied de page bleu marine). Sélecteur FR/EN intégré, langue détectée via `?lang=`.

## Placeholders à compléter par Marc avant mise en ligne

Les documents sources contiennent des `[crochets]` à remplir : nom de l'éditeur, courriel de contact,
responsable de la protection des renseignements personnels, nom de l'hébergeur, dates. Ils sont
reproduits tels quels dans les pages HTML.

## Déploiement Cloudflare Pages (à faire)

1. Créer un compte Cloudflare (gratuit) + acheter `hockey-dg.com` et `hockey-dg.ca`.
2. Dans Cloudflare : Workers & Pages → Create → Pages → Upload assets → glisser ce dossier.
3. Ajouter le domaine personnalisé `hockey-dg.com` (et redirection `hockey-dg.ca` → `hockey-dg.com`).
4. Mises à jour quotidiennes : régénérer `index.html`+`assets/` depuis le pipeline existant,
   relancer `build-legal.py` si les .md changent, puis ré-uploader (ou brancher un déploiement direct).

## Vérifications effectuées (2026-10-15)

- [x] Tous les chemins d'assets sont relatifs → fonctionnent depuis ce dossier
- [x] Les 4 pages servent en HTTP 200 via `python3 -m http.server`
- [x] Syntaxe JS validée (node --check) pour index.html et les 3 pages légales
- [x] Structure HTML validée (balises équilibrées)
- [x] Fidélité du contenu vérifiée par échantillonnage (phrases clés FR + EN présentes)
- [x] `artifact.share` jamais utilisé ; rien publié en ligne
