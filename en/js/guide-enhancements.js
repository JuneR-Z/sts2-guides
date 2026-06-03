/**
 * STS2Guides — Guide Page Enhancements
 * Auto-injects: Table of Contents, Related Guides, Back to Top button
 * Reduces bounce rate by keeping users engaged with content navigation.
 */
(function(){
'use strict';

/* ========== INJECT CSS ========== */
var css = document.createElement('style');
css.textContent = [
  '/* ToC Sidebar */',
  '#toc-container{background:var(--card,#1a1a30);border:1px solid var(--border,#2a2a45);border-radius:8px;padding:16px 20px;margin:0 0 28px;}',
  '#toc-container h4{color:var(--gold,#d4a03c);font-size:14px;margin:0 0 10px;text-transform:uppercase;letter-spacing:1px;}',
  '#toc-list{list-style:none;padding:0;margin:0;}',
  '#toc-list li{margin:4px 0;font-size:13px;line-height:1.5;}',
  '#toc-list a{color:var(--muted,#a09c8c);text-decoration:none;transition:color .15s;display:block;padding:3px 0;padding-left:0;}',
  '#toc-list a:hover{color:var(--gold-light,#f0c860);}',
  '#toc-list a.toc-h3{padding-left:16px;font-size:12px;}',
  '/* Related Guides */',
  '#related-guides{margin:40px 0 0;padding-top:24px;border-top:1px solid var(--border,#2a2a45);}',
  '#related-guides h3{color:var(--gold,#d4a03c);font-size:16px;margin:0 0 14px;}',
  '.related-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;}',
  '.related-card{background:var(--card,#1a1a30);border:1px solid var(--border,#2a2a45);border-radius:6px;padding:12px 14px;text-decoration:none;transition:border-color .15s,background .15s;}',
  '.related-card:hover{border-color:var(--gold,#d4a03c);background:rgba(212,160,60,.08);}',
  '.related-card .rc-title{color:var(--text,#e8e6dc);font-size:13px;font-weight:600;margin:0 0 4px;}',
  '.related-card .rc-meta{color:var(--muted,#a09c8c);font-size:11px;margin:0;}',
  '/* Back to Top */',
  '#back-to-top{position:fixed;bottom:28px;right:28px;width:40px;height:40px;background:var(--card,#1a1a30);border:1px solid var(--border,#2a2a45);border-radius:50%;color:var(--gold,#d4a03c);font-size:20px;cursor:pointer;display:none;align-items:center;justify-content:center;z-index:99;transition:all .2s;box-shadow:0 2px 8px rgba(0,0,0,.3);}',
  '#back-to-top:hover{background:var(--gold,#d4a03c);color:var(--bg,#0d0d1a);transform:translateY(-2px);}',
  '#back-to-top.show{display:flex;}',
  '@media(max-width:768px){.related-grid{grid-template-columns:1fr;}#back-to-top{bottom:16px;right:16px;}}'
].join('\n');
document.head.appendChild(css);

/* ========== TABLE OF CONTENTS ========== */
function buildToC(){
  var article = document.querySelector('article');
  if(!article) return;
  var headings = article.querySelectorAll('h2,h3');
  if(headings.length < 2) return;
  var container = document.createElement('div');
  container.id = 'toc-container';
  var html = '<h4>📑 In This Guide</h4><ul id="toc-list">';
  headings.forEach(function(h,i){
    var id = 'section-' + i;
    h.id = id;
    var cls = h.tagName === 'H3' ? ' class="toc-h3"' : '';
    html += '<li><a href="#' + id + '"' + cls + '>' + h.textContent + '</a></li>';
  });
  html += '</ul>';
  container.innerHTML = html;

  /* Insert after the meta line (date/read time/tags) */
  var meta = article.querySelector('p[style*="var(--muted)"]') || article.querySelector('h1 + p');
  if(meta && meta.nextSibling){
    meta.parentNode.insertBefore(container, meta.nextSibling);
  } else if(article.querySelector('h1')){
    var h1 = article.querySelector('h1');
    h1.parentNode.insertBefore(container, h1.nextSibling);
  }
}

/* ========== RELATED GUIDES ========== */
var relatedMap = {
  /* Character guides */
  ironclad: [
    {url:'../guides/ironclad-builds.html',title:'Ironclad Builds Compendium',meta:'7 builds · S-tier'},
    {url:'../guides/exhaust-synergy-guide.html',title:'Exhaust Synergy Guide',meta:'Corruption builds'},
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'A0→A10 strategy'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  silent: [
    {url:'../guides/silent-build-guide.html',title:'Silent Build Guide',meta:'Poison, Shiv, Discard'},
    {url:'../guides/coop-team-comps.html',title:'Co-op Team Comps',meta:'Silent synergies'},
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'A0→A10 strategy'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  defect: [
    {url:'../guides/ironclad-builds.html',title:'Ironclad Builds Compendium',meta:'7 builds'},
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'A0→A10 strategy'},
    {url:'../guides/relic-synergies-guide.html',title:'Relic Synergies Guide',meta:'Best combos'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  necrobinder: [
    {url:'../guides/coop-team-comps.html',title:'Co-op Team Comps',meta:'Necrobinder synergies'},
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'A0→A10 strategy'},
    {url:'../guides/ancient-boons-guide.html',title:'Ancient Boons Guide',meta:'Power scaling'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  regent: [
    {url:'../guides/regent-master-guide.html',title:'Regent Master Guide',meta:'Command & Sly strategy'},
    {url:'../guides/coop-team-comps.html',title:'Co-op Team Comps',meta:'Regent synergies'},
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'A0→A10 strategy'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  boss: [
    {url:'../guides/corrupted-heart-guide.html',title:'Corrupted Heart Guide',meta:'Act 4 boss strategy'},
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'A0→A10 strategy'},
    {url:'../guides/neow-bonus-guide.html',title:'Neow Bonus Guide',meta:'Starting bonus picks'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  coop: [
    {url:'../guides/silent-build-guide.html',title:'Silent Build Guide',meta:'Poison, Shiv, Discard'},
    {url:'../guides/relic-synergies-guide.html',title:'Relic Synergies Guide',meta:'Best combos'},
    {url:'../guides/defect-complete-guide.html',title:'Defect Complete Guide',meta:'Orbs & Focus'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  ascension: [
    {url:'../guides/enchantment-guide.html',title:'Enchantment Guide',meta:'Card upgrades'},
    {url:'../guides/card-removal-guide.html',title:'Card Removal Guide',meta:'Deck thinning'},
    {url:'../guides/neow-bonus-guide.html',title:'Neow Bonus Guide',meta:'Starting bonus picks'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ],
  beginner: [
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'Next step'},
    {url:'../guides/enchantment-guide.html',title:'Enchantment Guide',meta:'Card upgrades'},
    {url:'../guides/card-removal-guide.html',title:'Card Removal Guide',meta:'Deck thinning'},
    {url:'../guides/neow-bonus-guide.html',title:'Neow Bonus Guide',meta:'Starting bonus picks'}
  ],
  default: [
    {url:'../guides/ascension-climbing-guide.html',title:'Ascension Climbing Guide',meta:'A0→A10 strategy'},
    {url:'../guides/relic-synergies-guide.html',title:'Relic Synergies Guide',meta:'Best combos'},
    {url:'../guides/neow-bonus-guide.html',title:'Neow Bonus Guide',meta:'Starting bonus picks'},
    {url:'../guides/beginner.html',title:"Beginner's Guide",meta:'Start here'}
  ]
};

function buildRelated(){
  var article = document.querySelector('article');
  if(!article) return;
  var title = (document.title||'').toLowerCase();
  var h1 = (article.querySelector('h1')||{}).textContent||'';
  h1 = h1.toLowerCase();
  var combined = title + ' ' + h1;

  var key = 'default';
  if(combined.indexOf('ironclad')>-1) key='ironclad';
  else if(combined.indexOf('silent')>-1) key='silent';
  else if(combined.indexOf('defect')>-1) key='defect';
  else if(combined.indexOf('necrobinder')>-1) key='necrobinder';
  else if(combined.indexOf('regent')>-1) key='regent';
  else if(combined.indexOf('boss')>-1||combined.indexOf('heart')>-1||combined.indexOf('corrupt')>-1) key='boss';
  else if(combined.indexOf('co-op')>-1||combined.indexOf('coop')>-1||combined.indexOf('multiplayer')>-1) key='coop';
  else if(combined.indexOf('ascension')>-1||combined.indexOf('climbing')>-1||combined.indexOf('a10')>-1||combined.indexOf('a0')>-1) key='ascension';
  else if(combined.indexOf('beginner')>-1||combined.indexOf('new player')>-1) key='beginner';

  var guides = relatedMap[key] || relatedMap['default'];
  var container = document.createElement('div');
  container.id = 'related-guides';
  var html = '<h3>📖 Related Guides</h3><div class="related-grid">';
  guides.forEach(function(g){
    html += '<a href="' + g.url + '" class="related-card"><div class="rc-title">' + g.title + '</div><div class="rc-meta">' + g.meta + '</div></a>';
  });
  html += '</div>';
  container.innerHTML = html;
  article.appendChild(container);
}

/* ========== BACK TO TOP ========== */
function buildBackToTop(){
  var btn = document.createElement('button');
  btn.id = 'back-to-top';
  btn.innerHTML = '↑';
  btn.title = 'Back to top';
  btn.addEventListener('click',function(){
    window.scrollTo({top:0,behavior:'smooth'});
  });
  document.body.appendChild(btn);
  window.addEventListener('scroll',function(){
    btn.classList.toggle('show',window.scrollY > 400);
  });
}

/* ========== INIT ========== */
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',function(){
    buildToC();
    buildRelated();
    buildBackToTop();
  });
} else {
  buildToC();
  buildRelated();
  buildBackToTop();
}

})();
