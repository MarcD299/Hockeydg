#!/usr/bin/env python3
"""Convertit les .md légaux en pages HTML bilingues au style HockeyDG."""
import re, html, os

LEGAL_DIR = os.path.expanduser("~/workspace/research_notes/hockeydg-legal")
OUT_DIR = os.path.expanduser("~/workspace/hockeydg-deploy")

def esc(t):
    return html.escape(t, quote=False)

def inline_md(t):
    """Convertit le markdown inline : liens, gras, italique, code."""
    # D'abord échapper le HTML
    t = esc(t)
    # Liens [texte](url)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    # Gras **texte**
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    # Italique *texte* (éviter les ** déjà traités)
    t = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', t)
    # Code `texte`
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t

def md_to_html(md_text):
    """Convertit un bloc markdown (sans front-matter) en HTML."""
    lines = md_text.split("\n")
    out = []
    i = 0
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # Ligne vide
        if not s:
            close_list()
            i += 1
            continue
        # Séparateur
        if re.match(r'^---+$', s):
            close_list()
            out.append("<hr>")
            i += 1
            continue
        # Titres
        m = re.match(r'^(#{1,4})\s+(.*)', s)
        if m:
            close_list()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline_md(m.group(2))}</h{lvl}>")
            i += 1
            continue
        # Blockquote
        if s.startswith(">"):
            close_list()
            qs = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                qs.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + "<br>".join(inline_md(q) for q in qs) + "</blockquote>")
            continue
        # Tableau
        if "|" in s and i + 1 < len(lines) and re.match(r'^\s*\|?[\s:\-|]+\|?\s*$', lines[i+1]):
            close_list()
            headers = [c.strip() for c in s.strip("|").split("|")]
            i += 2  # sauter la ligne de séparation
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            tbl = ["<table><thead><tr>"] + [f"<th>{inline_md(h)}</th>" for h in headers] + ["</tr></thead><tbody>"]
            for r in rows:
                tbl.append("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in r) + "</tr>")
            tbl.append("</tbody></table>")
            out.append("".join(tbl))
            continue
        # Liste
        if re.match(r'^[-*]\s+', s):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_md(re.sub(r'^[-*]\s+', '', s))}</li>")
            i += 1
            continue
        # Liste numérotée
        if re.match(r'^\d+\.\s+', s):
            close_list()
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i].strip()):
                items.append(inline_md(re.sub(r'^\d+\.\s+', '', lines[i].strip())))
                i += 1
            out.append("<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>")
            continue
        # Paragraphe (regrouper les lignes consécutives)
        close_list()
        para = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,4}\s|[-*]\s|\d+\.\s|>|\||---+$)', lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + "<br>".join(inline_md(p) for p in para) + "</p>")
    close_list()
    return "\n".join(out)

def split_fr_en(md_text):
    """Sépare les versions FR et EN d'un document (séparateur '## ENGLISH VERSION' ou '---')."""
    # Retirer l'avertissement blockquote initial et le titre de projet
    text = md_text
    # Chercher le marqueur de version anglaise
    m = re.search(r'^## ENGLISH VERSION\s*$', text, re.M)
    if m:
        fr = text[:m.start()]
        en = text[m.end():]
        return fr.strip(), en.strip()
    return text.strip(), None

def clean_intro(text):
    """Retire le titre de projet, l'avertissement initial, le séparateur et
    les intertitres 'VERSION FRANÇAISE' / 'ENGLISH VERSION' (le sélecteur de
    langue de la page s'en charge déjà)."""
    lines = text.split("\n")
    out = []
    skip_blockquote = True
    for line in lines:
        s = line.strip()
        if skip_blockquote and (s.startswith(">") or not s):
            continue
        if re.match(r'^#\s+Projet de', s):
            continue
        if re.match(r'^---+$', s):
            continue
        if re.match(r'^##\s+(VERSION FRANÇAISE|ENGLISH VERSION)\s*$', s):
            skip_blockquote = False
            continue
        skip_blockquote = False
        out.append(line)
    return "\n".join(out).strip()

PAGE_TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="color-scheme" content="light" />
  <link rel="icon" type="image/webp" sizes="64x64" href="assets/hockeydg-logo-64.webp" />
  <title>{title} | HockeyDG</title>
  <meta name="description" content="{desc}" />
  <meta name="robots" content="index,follow" />
  <style>
    :root {{
      color-scheme: light;
      --paper:#f5f8fc; --surface:#ffffff; --surface-2:#eaf3fb;
      --ink:#07152d; --muted:#465a75; --line:#b9cee3;
      --red:#d7192d; --red-dark:#a80f24; --blue:#064a96;
      --ice:#d8ebfa; --sky:#b9d8f2; --sky-soft:#edf6fd; --navy:#021b46;
      --shadow:0 18px 50px rgba(4,25,37,.12);
    }}
    * {{ box-sizing:border-box; }}
    html[lang="en"] .lang-fr {{ display:none; }}
    html[lang="fr"] .lang-en {{ display:none; }}
    body {{ margin:0; background:var(--paper); color:var(--ink);
      font-family:"Source Sans 3",-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
      font-size:1rem; line-height:1.6; }}
    .wrap {{ width:min(860px,calc(100% - 36px)); margin-inline:auto; }}
    /* En-tête */
    .legal-header {{ background:var(--surface); border-bottom:4px solid var(--blue); }}
    .legal-header-inner {{ display:flex; align-items:center; gap:16px; padding:14px 0; flex-wrap:wrap; }}
    .legal-brand {{ display:flex; align-items:center; gap:12px; text-decoration:none; color:var(--ink); margin-right:auto; }}
    .legal-brand img {{ width:56px; height:56px; border-radius:50%; }}
    .legal-brand strong {{ font-size:1.35rem; color:var(--navy); }}
    .legal-brand strong span {{ color:var(--red); }}
    .legal-brand small {{ display:block; color:var(--muted); font-size:.82rem; font-weight:400; }}
    .back-link {{ display:inline-block; padding:9px 18px; border-radius:999px; background:var(--surface-2);
      color:var(--blue); font-weight:700; text-decoration:none; border:1px solid var(--line); }}
    .back-link:hover {{ background:var(--ice); }}
    .lang-switch {{ display:flex; gap:6px; }}
    .lang-btn {{ min-width:44px; min-height:38px; border:0; border-radius:999px; background:transparent;
      color:var(--muted); font-weight:700; cursor:pointer; font-size:.95rem; padding:6px 12px; }}
    .lang-btn[aria-pressed="true"] {{ background:var(--blue); color:#fff; }}
    /* Contenu */
    .legal-main {{ padding:34px 0 60px; }}
    .legal-card {{ background:var(--surface); border-radius:18px; box-shadow:var(--shadow);
      padding:clamp(22px,4vw,44px); border:1px solid var(--line); }}
    .legal-card h1 {{ color:var(--navy); font-size:clamp(1.5rem,3.4vw,2.1rem); margin:0 0 6px;
      padding-bottom:14px; border-bottom:3px solid var(--red); }}
    .legal-card h2 {{ color:var(--blue); font-size:1.18rem; margin:28px 0 8px; }}
    .legal-card h2::before {{ content:""; display:inline-block; width:8px; height:8px; border-radius:50%;
      background:var(--red); margin-right:10px; vertical-align:2px; }}
    .legal-card p, .legal-card li {{ color:var(--ink); }}
    .legal-card ul, .legal-card ol {{ padding-left:22px; }}
    .legal-card li {{ margin:6px 0; }}
    .legal-card a {{ color:var(--blue); }}
    .legal-card table {{ width:100%; border-collapse:collapse; margin:16px 0; font-size:.93rem;
      border-radius:12px; overflow:hidden; }}
    .legal-card th {{ background:var(--navy); color:#fff; text-align:left; padding:10px 12px; }}
    .legal-card td {{ padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
    .legal-card tr:nth-child(even) td {{ background:var(--sky-soft); }}
    .legal-card blockquote {{ background:var(--sky-soft); border-left:4px solid var(--blue);
      border-radius:0 12px 12px 0; padding:12px 16px; margin:16px 0; color:var(--muted); }}
    .legal-card hr {{ border:0; border-top:1px solid var(--line); margin:26px 0; }}
    .legal-card code {{ background:var(--surface-2); padding:2px 7px; border-radius:8px; font-size:.88em; }}
    .update-note {{ color:var(--muted); font-size:.92rem; margin:0 0 20px; }}
    .lang-divider {{ display:flex; align-items:center; gap:14px; margin:44px 0 8px; }}
    .lang-divider::before, .lang-divider::after {{ content:""; flex:1; border-top:2px solid var(--line); }}
    .lang-divider span {{ background:var(--navy); color:#fff; font-weight:700; padding:8px 22px; border-radius:999px; }}
    /* Pied de page */
    .site-footer {{ padding:26px 0; background:var(--navy); color:#fff; border-top:5px solid var(--red); }}
    .site-footer-inner {{ display:flex; flex-wrap:wrap; gap:14px 28px; align-items:center; justify-content:space-between; }}
    .footer-brand {{ display:flex; align-items:center; gap:12px; }}
    .footer-brand img {{ width:52px; height:52px; border-radius:50%; }}
    .footer-brand strong {{ display:block; font-size:1.1rem; }}
    .footer-brand span {{ font-size:.85rem; opacity:.8; }}
    .footer-links {{ display:flex; flex-wrap:wrap; gap:8px 20px; }}
    .footer-links a {{ color:#fff; text-decoration:none; font-size:.92rem; opacity:.92; }}
    .footer-links a:hover {{ text-decoration:underline; opacity:1; }}
    /* Bandeau témoins */
    .cookie-banner {{ position:fixed; left:12px; right:12px; bottom:12px; z-index:9999;
      background:var(--surface); border:1px solid var(--line); border-radius:16px;
      box-shadow:var(--shadow); padding:16px 18px; display:none; }}
    .cookie-banner.show {{ display:block; }}
    .cookie-banner p {{ margin:0 0 12px; font-size:.92rem; color:var(--muted); }}
    .cookie-banner p strong {{ color:var(--ink); }}
    .cookie-actions {{ display:flex; gap:10px; flex-wrap:wrap; }}
    .cookie-btn {{ border:0; border-radius:999px; padding:10px 22px; font-weight:700; cursor:pointer; font-size:.95rem; }}
    .cookie-accept {{ background:var(--blue); color:#fff; }}
    .cookie-decline {{ background:var(--surface-2); color:var(--blue); border:1px solid var(--line); }}
    .cookie-link {{ background:none; border:0; color:var(--blue); text-decoration:underline; cursor:pointer; font-size:.9rem; padding:10px 6px; }}
    @media (max-width:640px) {{
      .legal-header-inner {{ gap:10px; }}
      .cookie-banner {{ left:8px; right:8px; bottom:8px; }}
    }}
  </style>
</head>
<body>
  <header class="legal-header">
    <div class="wrap legal-header-inner">
      <a class="legal-brand" href="index.html" id="brandHome">
        <img src="assets/hockeydg-logo-128.webp" alt="Logo HockeyDG" width="56" height="56" />
        <span><strong>Hockey <span>DG</span></strong><small class="lang-fr">Le hockey, mesuré autrement</small><small class="lang-en">Hockey, measured differently</small></span>
      </a>
      <div class="lang-switch" role="group" aria-label="Langue / Language">
        <button class="lang-btn" type="button" data-lang="fr" aria-pressed="true">FR</button>
        <button class="lang-btn" type="button" data-lang="en" aria-pressed="false">EN</button>
      </div>
      <a class="back-link" href="index.html" id="backHome"><span class="lang-fr">← Retour au site</span><span class="lang-en">← Back to site</span></a>
    </div>
  </header>

  <main class="wrap legal-main">
    <article class="legal-card">
      <div class="lang-fr">{fr_html}</div>
      {en_block}
    </article>
  </main>

  <footer class="site-footer">
    <div class="wrap site-footer-inner">
      <div class="footer-brand">
        <img src="assets/hockeydg-logo-128.webp" alt="Logo HockeyDG" width="52" height="52" />
        <div><strong>HockeyDG</strong><span class="lang-fr">Le hockey, mesuré autrement</span><span class="lang-en">Hockey, measured differently</span></div>
      </div>
      <nav class="footer-links" aria-label="Liens légaux / Legal links">
        <a href="confidentialite.html"><span class="lang-fr">Confidentialité</span><span class="lang-en">Privacy</span></a>
        <a href="conditions.html"><span class="lang-fr">Conditions d'utilisation</span><span class="lang-en">Terms of Use</span></a>
        <a href="mentions-legales.html"><span class="lang-fr">Mentions légales</span><span class="lang-en">Legal Notice</span></a>
        <a href="https://www.facebook.com/share/19nkBv9xJt/" target="_blank" rel="noopener">Facebook</a>
      </nav>
    </div>
  </footer>

  <div class="cookie-banner" id="cookieBanner" role="dialog" aria-live="polite">
    <p><strong class="lang-fr">Nous respectons votre vie privée.</strong><strong class="lang-en">We respect your privacy.</strong><br />
    <span class="lang-fr">Nous utilisons des témoins strictement nécessaires au fonctionnement du site. La mesure d'audience et la publicité ne seront activées qu'avec votre consentement. <a href="confidentialite.html">En savoir plus</a></span><span class="lang-en">We use strictly necessary cookies for the site to operate. Analytics and advertising will only be enabled with your consent. <a href="confidentialite.html">Learn more</a></span></p>
    <div class="cookie-actions">
      <button class="cookie-btn cookie-accept" type="button" id="cookieAccept"><span class="lang-fr">Accepter</span><span class="lang-en">Accept</span></button>
      <button class="cookie-btn cookie-decline" type="button" id="cookieDecline"><span class="lang-fr">Refuser</span><span class="lang-en">Decline</span></button>
    </div>
  </div>

  <script>
  (function(){{
    function getLang(){{
      try {{
        var q = new URLSearchParams(window.location.search).get('lang');
        if (q === 'en' || q === 'fr') return q;
      }} catch(e) {{}}
      return document.documentElement.lang === 'en' ? 'en' : 'fr';
    }}
    function setLang(l){{
      document.documentElement.lang = l;
      document.querySelectorAll('.lang-btn').forEach(function(b){{
        b.setAttribute('aria-pressed', b.dataset.lang === l ? 'true' : 'false');
      }});
      var bh = document.getElementById('backHome');
      var br = document.getElementById('brandHome');
      if (bh) bh.href = 'index.html?lang=' + l;
      if (br) br.href = 'index.html?lang=' + l;
    }}
    var lang = getLang();
    setLang(lang);
    document.querySelectorAll('.lang-btn').forEach(function(b){{
      b.addEventListener('click', function(){{
        setLang(b.dataset.lang);
        var u = new URL(window.location.href);
        u.searchParams.set('lang', b.dataset.lang);
        history.replaceState(null, '', u.toString());
        propagateLang();
      }});
    }});
    /* Conserver la langue dans les liens internes */
    function propagateLang(){{
      var l = document.documentElement.lang === 'en' ? 'en' : 'fr';
      document.querySelectorAll('a[href$=".html"]').forEach(function(a){{
        var href = a.getAttribute('href');
        if (href && href.indexOf('?') === -1 && href.indexOf('://') === -1) {{
          a.setAttribute('href', href + '?lang=' + l);
        }}
      }});
    }}
    propagateLang();
    /* Bandeau témoins (Loi 25) */
    var KEY = 'hdg-cookie-consent';
    var banner = document.getElementById('cookieBanner');
    function showBanner(){{ banner.classList.add('show'); }}
    function hideBanner(v){{ try {{ localStorage.setItem(KEY, v); }} catch(e) {{}} banner.classList.remove('show'); }}
    var stored = null;
    try {{ stored = localStorage.getItem(KEY); }} catch(e) {{}}
    if (!stored) {{ showBanner(); }}
    document.getElementById('cookieAccept').addEventListener('click', function(){{ hideBanner('accepted'); }});
    document.getElementById('cookieDecline').addEventListener('click', function(){{ hideBanner('declined'); }});
    window.hdgReopenCookies = function(){{ showBanner(); }};
  }})();
  </script>
</body>
</html>
"""

# Traduction fidèle des mentions légales (le .md source est en français uniquement)
MENTIONS_EN = """# Legal Notice — HockeyDG.com

**Last updated:** [date]

---

## 1. Site publisher

**HockeyDG.com** — online sports media (hockey).
Published by: **[company / publisher name]**
[Legal form, e.g.: sole proprietorship registered in Quebec — NEQ: [number], if applicable]
Contact: [email] · [phone, optional] · [address, optional]

**Personal Information Protection Officer:** [name] — [dedicated email]
**Publication manager:** [name]

## 2. Hosting

[Host name] — [host address / website]

## 3. Intellectual property

The texts, analysis and original layout of HockeyDG.com are the property of [publisher name], unless stated otherwise. Any reproduction without written permission is prohibited, subject to the exceptions under Canada's *Copyright Act*. See our Terms of Use.

## 4. Photo credits

The photographs illustrating HockeyDG.com come from:

- **Wikimedia Commons** — photos under free Creative Commons licences (CC BY, CC BY-SA) or in the public domain. Each photo is credited individually (photographer, licence, link to the source) in accordance with its licence terms.
- **Getty Images** — photos embedded via the official "Embed from Getty Images" player, for editorial use, with automatic photographer credit and a link to Getty Images, in accordance with Getty Images' terms of use.

Copying or reusing images from the site is prohibited.

## 5. Sports data sources

Scores, standings, statistics and schedules are compiled from official sources, including:
- **NHL** — official API (api-web.nhle.com);
- **QMJHL, OHL, WHL, AHL, PWHL** — official data via HockeyTech / LeagueStat;
- **Liiga (Finland)** — liiga.fi;
- **KHL** — official data;
- **SHL, National League (Switzerland), NCAA** — official sources and licensed partners.

Raw data (scores, game facts) are public facts; their presentation on HockeyDG.com is original. Sources are mentioned in the relevant sections.

## 6. Advertising and audience measurement

[If applicable at the time of publication — otherwise delete this paragraph:]
The site displays advertisements provided by third parties (Google AdSense) and may use audience measurement tools. See our Privacy Policy for details on the cookies used and how to manage your consent.

## 7. Governing law

The site is published in Quebec, Canada. It is subject to the laws of Quebec and applicable federal Canadian laws, including the *Act respecting the protection of personal information in the private sector* (Law 25) and the *Copyright Act*.

## 8. Reporting

To report an error, a photo you hold the rights to, or to exercise your rights (access, rectification, complaint): [contact email] — response within 30 days for personal information requests.
"""

PAGES = [
    {
        "src": "politique-confidentialite-FR-EN.md",
        "out": "confidentialite.html",
        "title_fr": "Politique de confidentialité",
        "title_en": "Privacy Policy",
        "desc": "Politique de confidentialité de HockeyDG.com — renseignements recueillis, témoins, droits (Loi 25). Privacy Policy.",
    },
    {
        "src": "conditions-utilisation-FR-EN.md",
        "out": "conditions.html",
        "title_fr": "Conditions d'utilisation",
        "title_en": "Terms of Use",
        "desc": "Conditions d'utilisation de HockeyDG.com. Terms of Use.",
    },
    {
        "src": "mentions-legales.md",
        "out": "mentions-legales.html",
        "title_fr": "Mentions légales",
        "title_en": "Legal Notice",
        "desc": "Mentions légales, crédits et sources de HockeyDG.com. Legal notice, credits and sources.",
        "en_override": MENTIONS_EN,
    },
]

for p in PAGES:
    raw = open(os.path.join(LEGAL_DIR, p["src"]), encoding="utf-8").read()
    fr_raw, en_raw = split_fr_en(raw)
    fr_raw = clean_intro(fr_raw)
    fr_html = md_to_html(fr_raw)
    if p.get("en_override"):
        en_html = md_to_html(p["en_override"])
    elif en_raw:
        en_html = md_to_html(clean_intro(en_raw))
    else:
        en_html = None
    if en_html:
        en_block = (
            '<div class="lang-divider lang-en" aria-hidden="true"><span>ENGLISH</span></div>'
            '<div class="lang-divider lang-fr" aria-hidden="true"><span>ANGLAIS</span></div>'
            f'<div class="lang-en">{en_html}</div>'
        )
    else:
        en_block = ""
    page = PAGE_TEMPLATE.format(
        title=p["title_fr"] + " / " + p["title_en"],
        desc=p["desc"],
        fr_html=fr_html,
        en_block=en_block,
    )
    out_path = os.path.join(OUT_DIR, p["out"])
    open(out_path, "w", encoding="utf-8").write(page)
    print(f"OK: {p['out']} ({len(page)} octets)")
