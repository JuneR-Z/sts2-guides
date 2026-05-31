"""
Batch generate individual card & relic detail pages for STS2Guides.
Reads data from en/cards/cards-data.js and en/relics/relics-data.js,
generates one HTML file per card/relic.
"""
import json
import re
import os
import sys
from html import escape

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))

CHARACTER_ICONS = {
    'ironclad': '⚔️', 'silent': '🗡️', 'defect': '⚡',
    'necrobinder': '💀', 'regent': '👑',
    'colorless': '🎨', 'curse': '💀', 'status': '⚠️',
    'quest': '📜', 'token': '🃏'
}
CHARACTER_NAMES = {
    'ironclad': 'Ironclad', 'silent': 'Silent', 'defect': 'Defect',
    'necrobinder': 'Necrobinder', 'regent': 'Regent',
    'colorless': 'Colorless', 'curse': 'Curse', 'status': 'Status',
    'quest': 'Quest', 'token': 'Token'
}
# Characters that have their own guide/character page
HAS_CHAR_PAGE = {'ironclad', 'silent', 'defect', 'necrobinder', 'regent'}

def load_js_array(filepath):
    """Extract JSON array from a JS file.
    Supports both formats: const xxx = [...] and const xxx = {"value":[...]}"""
    with open(filepath, 'r', encoding='utf-8') as f:
        js = f.read()
    # Try new format first: {"value": [...]}
    match = re.search(r'=\s*(\{[\s\S]*\});?', js)
    if match:
        try:
            wrapper = json.loads(match.group(1))
            if isinstance(wrapper, dict) and 'value' in wrapper:
                return wrapper['value']
        except:
            pass
    # Fall back to old format: [...]
    match = re.search(r'=\s*(\[[\s\S]*\]);', js)
    if not match:
        raise ValueError(f"Cannot find array in {filepath}")
    return json.loads(match.group(1))


def slugify(name):
    """Convert card/relic name to URL-safe slug (same as data id)."""
    return name.lower().replace(' ', '_').replace("'", "").replace('?', '').replace('!', '')


def tier_color(tier):
    colors = {'S': 'var(--crimson)', 'A': 'var(--orange)', 'B': 'var(--gold)',
              'C': 'rgba(255,255,255,0.1)', 'D': 'rgba(255,255,255,0.05)',
              'F': 'rgba(255,255,255,0.03)', 'Starter': 'var(--green)'}
    return colors.get(tier, colors['C'])


def tier_text_color(tier):
    if tier in ('S', 'A', 'Starter'):
        return '#fff'
    if tier == 'B':
        return '#111'
    if tier == 'F':
        return 'var(--text-muted)'
    return 'var(--text-secondary)'


def clean_effect_text(text):
    """Remove game engine placeholders like {Damage:diff()} from text."""
    if not text:
        return text
    import re as _re
    return _re.sub(r'\{[^}]*\}', '...', text)


def generate_card_page(card):
    """Generate HTML for a single card detail page."""
    char = card['character']
    char_name = CHARACTER_NAMES.get(char, char.title())
    char_icon = CHARACTER_ICONS.get(char, '')
    page_id = card['id']
    name = card['name']
    tier = card['tier']
    ctype = card['type']
    rarity = card['rarity']
    cost = card['cost']
    effect = clean_effect_text(card['effect'])
    upgrade = clean_effect_text(card.get('upgrade', ''))
    reason = card.get('reason', '')
    strategy = card.get('strategy', '')

    # Avoid "Curse Curse Card" / "Status Status Card" redundancy
    if char_name == ctype:
        title = f"{name} — {ctype} Card | STS2Guides"
    else:
        title = f"{name} — {char_name} {ctype} Card | STS2Guides"
    
    desc = f"{name} is a {rarity} {ctype} card for {char_name} in Slay the Spire 2. "
    if cost == -1 and ctype in ('Curse', 'Status', 'Quest'):
        desc += "Unplayable. "
    else:
        desc += f"Costs {cost if cost != -1 else 'X'} Energy. "
    desc += effect
    if upgrade:
        desc += f" Upgraded: {upgrade}"

    # Clean up double-word redundancy in description
    desc = desc.replace('Curse Curse card for Curse', 'Curse card').replace('Status Status card for Status', 'Status card').replace('Quest Quest card for Quest', 'Quest card').replace('Token Token card for Token', 'Token card').replace('for Token in', 'in').replace('Unplayable. Unplayable.', 'Unplayable.')

    canonical = f"https://sts2guides.com/en/cards/{page_id}/"

    # Tier label
    tier_label = f"{tier}-Tier"
    if cost == -1 and ctype in ('Curse', 'Status', 'Quest'):
        cost_str = 'N/A'
        cost_display = '<div class="value">N/A</div>'
    elif cost == -1:
        cost_str = 'X'
        cost_display = f'<div class="value">X ⚡</div>'
    else:
        cost_str = str(cost)
        cost_display = f'<div class="value">{cost_str} ⚡</div>'

    # Effect highlighting
    effect_html = clean_effect_text(effect)
    # Highlight energy symbols
    effect_html = effect_html.replace('[E]', '<span class="energy">⚡</span>')
    effect_html = effect_html.replace('[S]', '<span class="star">⭐</span>')

    # Upgrade section
    upgrade_block = ''
    if upgrade:
        upgrade_text = upgrade
        upgrade_text = upgrade_text.replace('[E]', '⚡').replace('[S]', '⭐')
        upgrade_block = f'''
    <div class="detail-section">
      <h2>⬆️ Upgrade</h2>
      <p class="upgrade-text">{upgrade_text}</p>
    </div>'''

    # Tier reason
    reason_block = ''
    if reason:
        reason_block = f'''
    <div class="detail-section">
      <h2>📊 Tier Rating Rationale</h2>
      <p class="reason-text">{reason}</p>
    </div>'''

    # Strategy & Guide section
    strategy_block = ''
    if strategy:
        strategy_block = f'''
    <div class="detail-section">
      <h2>🧠 Strategy &amp; Tips</h2>
      <p class="strategy-text">{strategy}</p>
    </div>'''

    # Auto-generated "When to Pick" section based on card properties
    pick_advice_parts = []
    # Based on tier
    tier_advice = {
        'S': 'Almost always pick this card. It defines or enables a top-tier archetype and provides massive value in nearly every deck.',
        'A': 'Always consider this card. It is highly effective and fits into most decks without much setup.',
        'B': 'Situationally strong. Pick this when it fits your deck\'s strategy or you need its specific effect.',
        'C': 'Niche pick. Only take this if your deck specifically benefits from its effect or you have synergy relics.',
        'D': 'Generally skip. This card is underwhelming compared to alternatives, but may have rare use cases.',
        'F': 'Avoid picking. This card actively hurts your deck or is strictly worse than other options.',
        'Starter': 'You start with this card. Keep it unless you have a specific reason to remove it.'
    }
    if tier in tier_advice:
        pick_advice_parts.append(tier_advice[tier])

    # Based on type
    if ctype == 'Power':
        pick_advice_parts.append('As a Power card, it provides permanent value for the rest of combat. Prioritize playing it early in fights.')
    elif ctype == 'Attack':
        pick_advice_parts.append('As an Attack card, it directly contributes to your damage output. Evaluate if your deck needs more frontloaded damage or scaling damage.')
    elif ctype == 'Skill':
        pick_advice_parts.append('As a Skill card, it provides block, draw, or utility. Ensure your deck has a good balance of Skills and Attacks.')
    elif ctype == 'Curse':
        pick_advice_parts.append('Curse cards cannot be played and clutter your hand. Remove them at shops whenever possible.')
    elif ctype == 'Status':
        pick_advice_parts.append('Status cards are temporary effects added by enemies. They are unplayable and discarded at the end of combat.')

    # Based on cost
    if cost == 0:
        pick_advice_parts.append('Zero-cost cards are always efficient since they don\'t consume Energy. Great for triggering "on card played" effects and relics.')
    elif cost == 1:
        pick_advice_parts.append('One-cost cards are the backbone of most decks. They are easy to fit into any turn without straining your Energy budget.')
    elif cost == 2:
        pick_advice_parts.append('Two-cost cards require a moderate Energy investment. Ensure your deck has enough Energy generation to support them alongside other cards.')
    elif cost == 3:
        pick_advice_parts.append('Three-cost cards are expensive. You\'ll typically only play one per turn. Prioritize Energy relics and Energy-generating cards if you have multiple 3-cost cards.')
    elif cost == -1:
        pass  # X-cost or unplayable

    if pick_advice_parts:
        pick_html = '</p><p class="strategy-text">'.join(pick_advice_parts)
        strategy_block += f'''
    <div class="detail-section">
      <h2>🎯 When to Pick</h2>
      <p class="strategy-text">{pick_html}</p>
    </div>'''

    # Auto-generated synergy notes based on character and type
    synergy_notes = []
    char_synergies = {
        'ironclad': 'Ironclad excels at high-damage attacks and self-damage synergies. Cards that provide Strength scaling, exhaust effects, or healing pair well with Ironclad\'s kit.',
        'silent': 'Silent specializes in Shivs, Poison, and discard mechanics. Cards that generate multiple hits, apply debuffs, or enable cycling synergize with Silent\'s playstyle.',
        'defect': 'Defect focuses on Orb manipulation and Power scaling. Cards that generate or evoke Orbs, or provide Focus scaling, are central to Defect strategies.',
        'necrobinder': 'Necrobinder manipulates Doom stacks and executes. Cards that apply Doom, or trigger Death-knell effects, synergize with Necrobinder\'s unique mechanics.',
        'regent': 'Regent builds around Vows and channeling. Cards that interact with Vow stacks, or provide multi-turn payoffs, work well with Regent\'s playstyle.',
    }
    if char in char_synergies:
        synergy_notes.append(char_synergies[char])

    type_synergies = {
        'Attack': 'Attack cards benefit from Strength, Vulnerable, and damage-multiplying relics. Pair with energy-cheap Attacks for maximum efficiency.',
        'Skill': 'Skill cards benefit from Dexterity and block-scaling relics. Defensive Skills pair well with card draw to ensure you have block when needed.',
        'Power': 'Power cards scale permanently. Take relics that reduce setup time (like Bottles or innate effects) to play Powers before taking damage.',
    }
    if ctype in type_synergies:
        synergy_notes.append(type_synergies[ctype])

    if synergy_notes:
        synergy_html = '</p><p class="strategy-text">'.join(synergy_notes)
        strategy_block += f'''
    <div class="detail-section">
      <h2>🤝 Synergies</h2>
      <p class="strategy-text">{synergy_html}</p>
    </div>'''

    # Related cards (same character)
    char_links = ''
    if char in HAS_CHAR_PAGE:
        char_links = f'''
        <a href="../../characters/{char}.html">{char_icon} {char_name} Guide</a>
        <a href="../../guides/{char}-strength-build.html">{char_icon} {char_name} Builds</a>'''
    related_block = f'''
    <div class="detail-section">
      <h2>🔗 Related</h2>
      <div class="related-links">{char_links}
        <a href="../">📋 All Cards</a>
      </div>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="apple-touch-icon" href="/favicon.svg">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="STS2Guides">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<link rel="canonical" href="{canonical}">
<style>
:root {{
  --bg-primary: #0d0d1a; --bg-secondary: #151528; --bg-card: #1a1a30;
  --bg-card-hover: #222240; --border: #2a2a45;
  --text-primary: #e8e6dc; --text-secondary: #a09c8c; --text-muted: #686450;
  --gold: #d4a03c; --gold-light: #f0c860;
  --crimson: #c0392b; --green: #27ae60; --blue: #3498db; --purple: #8e44ad; --orange: #e67e22;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background: var(--bg-primary); color: var(--text-primary); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; min-height: 100vh; }}
header {{ background: var(--bg-secondary); border-bottom: 2px solid var(--gold); position: sticky; top:0; z-index:100; }}
.header-inner {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; height: 60px; }}
.logo {{ display: flex; align-items: center; gap: 10px; text-decoration: none; }}
.logo-icon {{ width: 36px; height: 36px; background: linear-gradient(135deg, var(--gold), var(--crimson)); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 20px; }}
.logo-text {{ font-size: 18px; font-weight: 700; color: var(--text-primary); }}
.logo-text span {{ color: var(--gold-light); }}
nav {{ display: flex; gap: 0; }}
nav a {{ color: var(--text-secondary); text-decoration: none; padding: 8px 14px; font-size: 13px; border-radius: 4px; transition: all .2s; }}
nav a:hover {{ color: var(--gold-light); background: rgba(255,255,255,0.05); }}
nav a.active {{ color: var(--gold-light); }}
.breadcrumb {{ max-width: 900px; margin: 0 auto; padding: 12px 20px; font-size: 13px; color: var(--text-muted); }}
.breadcrumb a {{ color: var(--text-secondary); text-decoration: none; }}
.breadcrumb a:hover {{ color: var(--gold-light); }}
main {{ max-width: 900px; margin: 0 auto; padding: 30px 20px; }}
.card-detail {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 32px; }}
.card-header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }}
.card-header h1 {{ font-size: 26px; font-weight: 800; }}
.tier-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: 800; font-size: 14px; background: {tier_color(tier)}; color: {tier_text_color(tier)}; }}
.char-tag {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 13px; background: rgba(255,255,255,0.08); color: var(--text-secondary); }}
.meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 24px; }}
.meta-item {{ background: var(--bg-secondary); border-radius: 8px; padding: 14px; }}
.meta-item .label {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
.meta-item .value {{ font-size: 16px; font-weight: 600; }}
.meta-item .value.rarity-common {{ color: var(--text-secondary); }}
.meta-item .value.rarity-uncommon {{ color: var(--blue); }}
.meta-item .value.rarity-rare {{ color: var(--gold-light); }}
.meta-item .value.rarity-basic {{ color: var(--text-muted); }}
.meta-item .value.rarity-ancient {{ color: var(--purple); }}
.meta-item .value.rarity-special {{ color: var(--orange); }}
.meta-item .value.rarity-curse {{ color: var(--crimson); }}
.meta-item .value.rarity-status {{ color: #888; }}
.meta-item .value.rarity-quest {{ color: var(--gold-light); }}
.meta-item .value.rarity-token {{ color: var(--green); }}
.meta-item .value.rarity-deprecated {{ color: var(--text-muted); }}
.meta-item .value.type-attack {{ color: var(--crimson); }}
.meta-item .value.type-skill {{ color: var(--green); }}
.meta-item .value.type-power {{ color: var(--purple); }}
.meta-item .value.type-curse {{ color: var(--crimson); }}
.meta-item .value.type-status {{ color: #888; }}
.meta-item .value.type-quest {{ color: var(--gold-light); }}
.detail-section {{ margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--border); }}
.detail-section h2 {{ font-size: 18px; font-weight: 700; margin-bottom: 12px; }}
.effect-text {{ font-size: 16px; color: var(--text-secondary); line-height: 1.7; }}
.upgrade-text {{ font-size: 16px; color: var(--gold-light); line-height: 1.7; }}
.reason-text {{ font-size: 15px; color: var(--text-muted); line-height: 1.6; }}
.strategy-text {{ font-size: 15px; color: var(--text-secondary); line-height: 1.7; }}
.energy {{ color: var(--gold-light); font-weight: 600; }}
.star {{ color: #e6a750; font-weight: 600; }}
.related-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.related-links a {{ display: inline-block; padding: 8px 16px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; color: var(--text-secondary); text-decoration: none; font-size: 13px; transition: all .2s; }}
.related-links a:hover {{ border-color: var(--gold); color: var(--gold-light); background: var(--bg-card-hover); }}
footer {{ background: var(--bg-secondary); border-top: 1px solid var(--border); padding: 30px 20px; margin-top: 40px; text-align: center; color: var(--text-muted); font-size: 12px; }}
footer a {{ color: var(--text-secondary); text-decoration: none; }}
footer a:hover {{ color: var(--gold-light); }}
.footer-links {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 12px; flex-wrap: wrap; }}
@media (max-width: 768px) {{
  .card-header h1 {{ font-size: 20px; }}
  .card-detail {{ padding: 20px; }}
  nav {{ display: none; }}
}}
@media (max-width: 900px) {{
  .header-inner {{ flex-wrap:wrap; height:auto; padding:8px 12px; gap:8px; }}
  .logo {{ order:1; }}
  .logo-text {{ font-size:15px; }}
  nav {{ order:3; width:100%; overflow-x:auto; justify-content:flex-start; padding:4px 0; }}
  nav a {{ font-size:12px; padding:6px 10px; white-space:nowrap; }}
}}
</style>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{name} — {char_name} {ctype} Card",
  "description": "{desc}",
  "url": "{canonical}",
  "isPartOf": {{
    "@type": "WebSite",
    "name": "STS2Guides",
    "url": "https://sts2guides.com/"
  }},
  "about": {{
    "@type": "Thing",
    "name": "Slay the Spire 2"
  }}
}}
</script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-L97YHHQRT3"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-L97YHHQRT3');
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
</head>
<body>

<header>
  <div class="header-inner">
    <a href="../../" class="logo"><div class="logo-icon">🗡️</div><div class="logo-text">STS2<span>Guides</span></div></a>
    <nav>
      <a href="../../">Home</a>
      <a href="../../guides/index.html">Guides</a>
      <a href="../../characters/index.html">Characters</a>
      <a href="../" class="active">Cards</a>
      <a href="../../tier-list/">Tier List</a>
      <a href="../../deck-builder/">Deck Builder</a>
      <a href="../../tools/">Tools</a>
      <a href="../../relics/index.html">Relics</a>
      <a href="../../bosses/index.html">Bosses</a>
      <a href="../../patch-notes/">Patch Notes</a>
      <a href="../../about.html">About</a>
    </nav>
  </div>
</header>

<div class="breadcrumb"><a href="../../">Home</a> › <a href="../">Cards</a> › {name}</div>

<main>
  <div class="card-detail">
    <div class="card-header">
      <h1>{name}</h1>
      <span class="tier-badge">{tier_label}</span>
      <span class="char-tag">{char_icon} {char_name}</span>
    </div>

    <div class="meta-grid">
      <div class="meta-item">
        <div class="label">Type</div>
        <div class="value type-{ctype.lower()}">{ctype}</div>
      </div>
      <div class="meta-item">
        <div class="label">Rarity</div>
        <div class="value rarity-{rarity.lower()}">{rarity}</div>
      </div>
      <div class="meta-item">
        <div class="label">Cost</div>
        {cost_display}
      </div>
      <div class="meta-item">
        <div class="label">Tier</div>
        <div class="value">{tier}-Tier</div>
      </div>
    </div>

    <div class="detail-section">
      <h2>📝 Effect</h2>
      <p class="effect-text">{effect_html}</p>
    </div>
{upgrade_block}
{reason_block}
{strategy_block}
{related_block}
  </div>
</main>

<footer>
  <div class="footer-links">
    <a href="../../">Home</a><a href="../../characters/index.html">Characters</a>
    <a href="../">Cards</a><a href="../../tier-list/">Tier List</a>
    <a href="../../deck-builder/">Deck Builder</a><a href="../../tools/">Tools</a>
    <a href="../../relics/index.html">Relics</a><a href="../../patch-notes/">Patch Notes</a><a href="../../about.html">About</a><a href="../../privacy.html">Privacy</a>
  </div>
  <p>STS2Guides is an unofficial, fan-made community site. Slay the Spire 2 is developed by Mega Crit Games.<br>This site is not affiliated with or endorsed by Mega Crit. © 2026 STS2Guides.</p>
  <p>DMCA / Copyright inquiries: <a href="mailto:dmca@sts2guides.com">dmca@sts2guides.com</a></p>
</footer>

</body>
</html>'''
    return html


def generate_relic_page(relic):
    """Generate HTML for a single relic detail page."""
    page_id = relic['id']
    name = relic['name']
    tier = relic['tier']
    character = relic.get('character', 'all')
    effect = relic['effect']
    comment = relic.get('comment', '')
    is_boss = relic.get('isBoss', False)

    # Character label
    if character == 'all':
        char_label = 'Universal (All Characters)'
        char_icon = '🌐'
    else:
        char_label = CHARACTER_NAMES.get(character, character.title())
        char_icon = CHARACTER_ICONS.get(character, '')

    tier_label = "Starter Relic" if tier == 'Starter' else f"{tier}-Tier"
    boss_tag = ' (Boss Relic)' if is_boss else ''

    title = f"{name}{boss_tag} — Relic | STS2Guides"
    tier_name = 'starter relic' if tier == 'Starter' else f'{tier}-tier relic'
    desc = f"{name} is a {tier_name} in Slay the Spire 2. "
    desc += f"{effect}"
    if comment:
        desc += f" Tip: {comment}"

    canonical = f"https://sts2guides.com/en/relics/{page_id}/"

    # Effect highlighting
    effect_html = effect
    effect_html = effect_html.replace('[E]', '<span class="energy">⚡</span>')
    effect_html = effect_html.replace('[S]', '<span class="star">⭐</span>')

    # Comment section
    comment_block = ''
    if comment:
        comment_text = comment.replace('[E]', '⚡').replace('[S]', '⭐')
        comment_block = f'''
    <div class="detail-section">
      <h2>💡 Strategy Note</h2>
      <p class="comment-text">{comment_text}</p>
    </div>'''

    # Boss tag in header
    boss_header = ' <span class="boss-tag">Boss Relic</span>' if is_boss else ''

    # Related
    char_link = ''
    if character != 'all':
        char_link = f'<a href="../../characters/{character}.html">{char_icon} {char_label} Guide</a>'
    related_block = f'''
    <div class="detail-section">
      <h2>🔗 Related</h2>
      <div class="related-links">
        {char_link}
        <a href="../">📋 All Relics</a>
        <a href="../../tier-list/">🏆 Tier List</a>
      </div>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="apple-touch-icon" href="/favicon.svg">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="STS2Guides">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<link rel="canonical" href="{canonical}">
<style>
:root {{
  --bg-primary: #0d0d1a; --bg-secondary: #151528; --bg-card: #1a1a30;
  --bg-card-hover: #222240; --border: #2a2a45;
  --text-primary: #e8e6dc; --text-secondary: #a09c8c; --text-muted: #686450;
  --gold: #d4a03c; --gold-light: #f0c860;
  --crimson: #c0392b; --green: #27ae60; --blue: #3498db; --purple: #8e44ad; --orange: #e67e22;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background: var(--bg-primary); color: var(--text-primary); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; min-height: 100vh; }}
header {{ background: var(--bg-secondary); border-bottom: 2px solid var(--gold); position: sticky; top:0; z-index:100; }}
.header-inner {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; height: 60px; }}
.logo {{ display: flex; align-items: center; gap: 10px; text-decoration: none; }}
.logo-icon {{ width: 36px; height: 36px; background: linear-gradient(135deg, var(--gold), var(--crimson)); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 20px; }}
.logo-text {{ font-size: 18px; font-weight: 700; color: var(--text-primary); }}
.logo-text span {{ color: var(--gold-light); }}
nav {{ display: flex; gap: 0; }}
nav a {{ color: var(--text-secondary); text-decoration: none; padding: 8px 14px; font-size: 13px; border-radius: 4px; transition: all .2s; }}
nav a:hover {{ color: var(--gold-light); background: rgba(255,255,255,0.05); }}
nav a.active {{ color: var(--gold-light); }}
.breadcrumb {{ max-width: 900px; margin: 0 auto; padding: 12px 20px; font-size: 13px; color: var(--text-muted); }}
.breadcrumb a {{ color: var(--text-secondary); text-decoration: none; }}
.breadcrumb a:hover {{ color: var(--gold-light); }}
main {{ max-width: 900px; margin: 0 auto; padding: 30px 20px; }}
.relic-detail {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 32px; }}
.relic-header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }}
.relic-header h1 {{ font-size: 26px; font-weight: 800; }}
.tier-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: 800; font-size: 14px; background: {tier_color(tier)}; color: {tier_text_color(tier)}; }}
.char-tag {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 13px; background: rgba(255,255,255,0.08); color: var(--text-secondary); }}
.boss-tag {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 12px; background: rgba(212,160,60,0.15); color: var(--gold-light); }}
.meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 24px; }}
.meta-item {{ background: var(--bg-secondary); border-radius: 8px; padding: 14px; }}
.meta-item .label {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
.meta-item .value {{ font-size: 16px; font-weight: 600; }}
.detail-section {{ margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--border); }}
.detail-section h2 {{ font-size: 18px; font-weight: 700; margin-bottom: 12px; }}
.effect-text {{ font-size: 16px; color: var(--text-secondary); line-height: 1.7; }}
.comment-text {{ font-size: 15px; color: var(--gold-light); line-height: 1.6; font-style: italic; }}
.energy {{ color: var(--gold-light); font-weight: 600; }}
.star {{ color: #e6a750; font-weight: 600; }}
.related-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.related-links a {{ display: inline-block; padding: 8px 16px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; color: var(--text-secondary); text-decoration: none; font-size: 13px; transition: all .2s; }}
.related-links a:hover {{ border-color: var(--gold); color: var(--gold-light); background: var(--bg-card-hover); }}
footer {{ background: var(--bg-secondary); border-top: 1px solid var(--border); padding: 30px 20px; margin-top: 40px; text-align: center; color: var(--text-muted); font-size: 12px; }}
footer a {{ color: var(--text-secondary); text-decoration: none; }}
footer a:hover {{ color: var(--gold-light); }}
.footer-links {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 12px; flex-wrap: wrap; }}
@media (max-width: 768px) {{
  .relic-header h1 {{ font-size: 20px; }}
  .relic-detail {{ padding: 20px; }}
  nav {{ display: none; }}
}}
@media (max-width: 900px) {{
  .header-inner {{ flex-wrap:wrap; height:auto; padding:8px 12px; gap:8px; }}
  .logo {{ order:1; }}
  .logo-text {{ font-size:15px; }}
  nav {{ order:3; width:100%; overflow-x:auto; justify-content:flex-start; padding:4px 0; }}
  nav a {{ font-size:12px; padding:6px 10px; white-space:nowrap; }}
}}
</style>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{name}{boss_tag} — Relic",
  "description": "{desc}",
  "url": "{canonical}",
  "isPartOf": {{
    "@type": "WebSite",
    "name": "STS2Guides",
    "url": "https://sts2guides.com/"
  }},
  "about": {{
    "@type": "Thing",
    "name": "Slay the Spire 2"
  }}
}}
</script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-L97YHHQRT3"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-L97YHHQRT3');
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
</head>
<body>

<header>
  <div class="header-inner">
    <a href="../../" class="logo"><div class="logo-icon">🗡️</div><div class="logo-text">STS2<span>Guides</span></div></a>
    <nav>
      <a href="../../">Home</a>
      <a href="../../guides/index.html">Guides</a>
      <a href="../../characters/index.html">Characters</a>
      <a href="../../cards/index.html">Cards</a>
      <a href="../../tier-list/">Tier List</a>
      <a href="../../deck-builder/">Deck Builder</a>
      <a href="../../tools/">Tools</a>
      <a href="../" class="active">Relics</a>
      <a href="../../bosses/index.html">Bosses</a>
      <a href="../../patch-notes/">Patch Notes</a>
      <a href="../../about.html">About</a>
    </nav>
  </div>
</header>

<div class="breadcrumb"><a href="../../">Home</a> › <a href="../">Relics</a> › {name}</div>

<main>
  <div class="relic-detail">
    <div class="relic-header">
      <h1>{name}{boss_header}</h1>
      <span class="tier-badge">{tier_label}</span>
      <span class="char-tag">{char_icon} {char_label}</span>
    </div>

    <div class="meta-grid">
      <div class="meta-item">
        <div class="label">Tier</div>
        <div class="value">{tier_label}</div>
      </div>
      <div class="meta-item">
        <div class="label">Character</div>
        <div class="value">{char_label}</div>
      </div>
    </div>

    <div class="detail-section">
      <h2>📝 Effect</h2>
      <p class="effect-text">{effect_html}</p>
    </div>
{comment_block}
{related_block}
  </div>
</main>

<footer>
  <div class="footer-links">
    <a href="../../">Home</a><a href="../../guides/index.html">Guides</a>
    <a href="../../characters/index.html">Characters</a><a href="../../cards/index.html">Cards</a>
    <a href="../../tier-list/">Tier List</a><a href="../../deck-builder/">Deck Builder</a>
    <a href="../../tools/">Tools</a><a href="../">Relics</a>
    <a href="../../bosses/index.html">Bosses</a><a href="../../patch-notes/">Patch Notes</a><a href="../../about.html">About</a><a href="../../privacy.html">Privacy</a>
  </div>
  <p>STS2Guides is an unofficial, fan-made community site. Slay the Spire 2 is developed by Mega Crit Games.<br>This site is not affiliated with or endorsed by Mega Crit. © 2026 STS2Guides.</p>
  <p>DMCA / Copyright inquiries: <a href="mailto:dmca@sts2guides.com">dmca@sts2guides.com</a></p>
</footer>

</body>
</html>'''
    return html


def generate_all():
    # Load data
    cards = load_js_array(os.path.join(BASE, 'en', 'cards', 'cards-data.js'))
    relics = load_js_array(os.path.join(BASE, 'en', 'relics', 'relics-data.js'))

    print(f"Loaded {len(cards)} cards, {len(relics)} relics")

    # --- Note about directory structure ---
    # Cards -> en/cards/{id}.html
    # Relics -> en/relics/{id}.html
    # But to have clean URLs like /en/cards/ironclad_anger/, we need
    # en/cards/ironclad_anger/index.html
    # Let's use directory-per-page approach for clean URLs

    card_dir = os.path.join(BASE, 'en', 'cards')
    relic_dir = os.path.join(BASE, 'en', 'relics')

    # Generate card pages
    card_count = 0
    for card in cards:
        dir_path = os.path.join(card_dir, card['id'])
        os.makedirs(dir_path, exist_ok=True)
        html = generate_card_page(card)
        with open(os.path.join(dir_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        card_count += 1
        if card_count % 50 == 0:
            print(f"  Generated {card_count}/{len(cards)} card pages...")

    print(f"✓ Generated {card_count} card detail pages in en/cards/")

    # Generate relic pages
    relic_count = 0
    for relic in relics:
        dir_path = os.path.join(relic_dir, relic['id'])
        os.makedirs(dir_path, exist_ok=True)
        html = generate_relic_page(relic)
        with open(os.path.join(dir_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        relic_count += 1
        if relic_count % 50 == 0:
            print(f"  Generated {relic_count}/{len(relics)} relic pages...")

    print(f"✓ Generated {relic_count} relic detail pages in en/relics/")

    # Generate sitemap entries
    sitemap_entries = []
    for card in cards:
        sitemap_entries.append(
            f'  <url><loc>https://sts2guides.com/en/cards/{card["id"]}/</loc>'
            f'<changefreq>monthly</changefreq><priority>0.7</priority></url>'
        )
    for relic in relics:
        sitemap_entries.append(
            f'  <url><loc>https://sts2guides.com/en/relics/{relic["id"]}/</loc>'
            f'<changefreq>monthly</changefreq><priority>0.7</priority></url>'
        )

    sitemap_path = os.path.join(BASE, 'sitemap_entries.txt')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sitemap_entries))
    print(f"✓ Wrote {len(sitemap_entries)} sitemap entries to sitemap_entries.txt")
    print(f"  → Review & insert these into sitemap.xml")
    print(f"\n🎉 Done! Generated {card_count} card + {relic_count} relic = {card_count + relic_count} total pages")


if __name__ == '__main__':
    generate_all()
