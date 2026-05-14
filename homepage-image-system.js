// Homepage image resolver for visible cards and pick archive cards.
// Keep this deterministic: use approved article-specific images first, then
// category-safe fallbacks only. Do not keyword-map to unrelated old assets.
(function() {
  var CATEGORY_STYLES = {
    NHL: { primary: '#0ea5e9', secondary: '#082f49', accent: '#dbeafe' },
    MLB: { primary: '#ef4444', secondary: '#4c0519', accent: '#fee2e2' },
    NBA: { primary: '#f97316', secondary: '#431407', accent: '#ffedd5' },
    NCAAB: { primary: '#8b5cf6', secondary: '#2e1065', accent: '#ede9fe' },
    NCAAF: { primary: '#16a34a', secondary: '#052e16', accent: '#dcfce7' },
    NFL: { primary: '#16a34a', secondary: '#052e16', accent: '#dcfce7' },
    Soccer: { primary: '#22c55e', secondary: '#052e16', accent: '#dcfce7' },
    Betting: { primary: '#f59e0b', secondary: '#451a03', accent: '#fef3c7' }
  };

  var TOPIC_LABELS = {
    Archive: 'ARCHIVE',
    BettingTools: 'TOOLS',
    Guide: 'GUIDE',
    Parlay: 'PARLAY',
    Pro: 'PRO',
    Records: 'RECORDS'
  };

  var SECTION_LABELS = {
    board: 'TODAY\'S BOARD',
    article: 'LATEST ARTICLE',
    path: 'SITE PATH',
    media: 'INTELLIGENCE',
    pick: 'PICK ARCHIVE'
  };

  var STATIC_CARD_META = {
    'board-bayern-real': {
      sport: 'Soccer',
      title: 'Bayern vs Real Madrid',
      kicker: 'Champions League quarterfinal matchup',
      badge: 'TODAY\'S BOARD'
    },
    'board-play-in-pressure': {
      sport: 'NBA',
      title: 'Play-In elimination pressure',
      kicker: 'Injury context, urgency, and market notes',
      badge: 'TODAY\'S BOARD'
    },
    'board-mlb-hub': {
      sport: 'MLB',
      title: 'Daily baseball preview hub',
      kicker: 'Pitchers, weather, totals, and bullpen context',
      badge: 'TODAY\'S BOARD'
    },
    'article-nba-play-in': {
      sport: 'NBA',
      title: 'NBA Play-In Tournament full preview',
      kicker: 'Bracket impact, injuries, and matchup context',
      badge: 'LATEST ARTICLE'
    },
    'article-world-cup-guide': {
      sport: 'Soccer',
      title: '2026 FIFA World Cup betting guide',
      kicker: 'Futures, groups, structure, and dark horses',
      badge: 'GUIDE'
    },
    'article-hub-guide': {
      sport: 'Betting',
      title: 'How to use the Handicapping Hub',
      kicker: 'Research workflow, tools, and betting process',
      badge: 'GUIDE'
    },
    'path-best-bets': {
      sport: 'Betting',
      title: 'Best Bets Today',
      kicker: 'Current picks and priority betting angles',
      badge: 'SITE PATH'
    },
    'path-pick-archive': {
      sport: 'Betting',
      title: 'Pick Archive',
      kicker: 'Historical picks and long-tail analysis',
      badge: 'ARCHIVE'
    },
    'path-moneyline-parlay': {
      sport: 'Betting',
      title: 'Moneyline Parlay',
      kicker: 'Daily parlay card and supporting context',
      badge: 'PARLAY'
    },
    'path-pro-tools': {
      sport: 'Betting',
      title: 'Pro Tools',
      kicker: 'Premium dashboards and model workflows',
      badge: 'PRO'
    },
    'media-nhl': {
      sport: 'NHL',
      title: 'NHL Previews',
      kicker: 'Goalies, special teams, and puck-line context',
      badge: 'INTELLIGENCE'
    },
    'media-nfl': {
      sport: 'NFL',
      title: 'NFL Picks',
      kicker: 'Situational edges, pricing, and matchup notes',
      badge: 'INTELLIGENCE'
    },
    'media-soccer': {
      sport: 'Soccer',
      title: 'Soccer Board',
      kicker: 'Form, xG, league spots, and marquee fixtures',
      badge: 'INTELLIGENCE'
    },
    'media-betting-tools': {
      sport: 'Betting',
      title: 'Betting Tools',
      kicker: 'Calculators, bankroll, and EV resources',
      badge: 'TOOLS'
    }
  };

  var BLOCKED_IMAGE_RE = /(?:arbitrage|allstars|fifa\.png|moneyview|money-logo|collegeban|LIVE\.png|ai-moneyball|mlb-picks-team-logos|homepage-preview|media\.d3\.nhle\.com|vegas-golden-knights)/i;

  var PICK_IMAGE_OVERRIDES = {
    'ducks-team-total-under-3-5-golden-knights-game-6-nhl-pick-may-14-2026.html': 'images/ducks-puck-line-plus-1-5-game-4-oilers-honda-center-nhl.jpg',
    'canadiens-sabres-game-5-featured-game-of-the-day.html': 'images/sabres-celebration-bruins-game-3-april-23-2026.jpg',
    'canadiens-sabres-golden-knights-ducks-nhl-playoff-preview.html': 'images/sabres-celebration-bruins-game-3-april-23-2026.jpg',
    'mlb-preview-today-eleven-game-board-betting-analysis.html': 'images/mlb-great-american-ballpark-yankees-reds.webp',
    'nba-playoff-reset-cavaliers-pistons-spurs-timberwolves-game-six.html': 'images/thunderwin.webp',
    'vegas-golden-knights-moneyline-minus-150-ducks-game-5-nhl-pick.html': 'images/ducks-puck-line-plus-1-5-game-4-oilers-honda-center-nhl.jpg',
    'thunder-sweep-watch-pistons-cavs-game-4-east-west-semis-nba.html': 'images/thunderwin.webp',
    'lakers-plus-11-thunder-game-4-elimination-spot-nba-pick.html': 'images/thunderwin.webp',
    'avalanche-vs-wild-nhl-western-semis-game-4-analysis-stats-preview.html': 'images/nhl-avalanche-utah-road-matchup-oct-21-2025.webp',
    'avalanche-wild-game-4-pivot-second-round-monday-nhl.html': 'images/nhl-avalanche-utah-road-matchup-oct-21-2025.webp',
    'sasaki-kirby-rasmussen-eovaldi-monday-six-pack-mlb.html': 'images/mlb-bryan-woo-mariners-yankees-pitching.webp',
    'sunday-fifteen-game-mlb-preview-may-10-2026.html': 'images/mlb-great-american-ballpark-yankees-reds.webp',
    'sabres-canadiens-knights-ducks-game-3-4-nhl-may-10-2026.html': 'images/sabres-celebration-bruins-game-3-april-23-2026.jpg',
    'knicks-76ers-spurs-wolves-game-4-east-west-semis-nba-may-10-2026.html': 'images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.webp',
    'pistons-vs-cavaliers-eastern-semis-game-3-analysis-stats-preview-may-9-2026.html': 'images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.webp',
    'hurricanes-flyers-avalanche-wild-nhl-may-9-2026.html': 'images/boston-bruins-carolina-hurricanes-nhl-betting-pick-november-17-2025.webp',
    'knicks-vs-76ers-eastern-semis-game-3-analysis-stats-preview-may-8-2026.html': 'images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.webp',
    'sale-fried-friday-fifteen-game-slate-mlb-may-8-2026.html': 'images/mlb-spencer-strider-braves-mets-f5-under.webp',
    'sabres-canadiens-knights-ducks-second-round-game-fest-nhl-may-8-2026.html': 'images/sabres-celebration-bruins-game-3-april-23-2026.jpg',
    'knicks-76ers-spurs-wolves-game-3-east-west-semis-nba-may-8-2026.html': 'images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.webp',
    'dortmund-frankfurt-bundesliga-levante-osasuna-laliga-soccer-may-8-2026.html': 'images/soccer-armenia-ireland-corner-betting-oct-14-2025.webp',
    'thunder-cavaliers-2-0-leads-east-west-semis-nba-may-7-2026.html': 'images/thunderwin.webp',
    'hurricanes-flyers-game-3-second-round-nhl-may-7-2026.html': 'images/boston-bruins-carolina-hurricanes-nhl-betting-pick-november-17-2025.webp',
    'gore-blackburn-yankees-rangers-thursday-mlb-may-7-2026.html': 'images/mlb-aaron-judge-yankees-batting.webp',
    'sabres-host-canadiens-game-1-knights-host-ducks-game-2-nhl.html': 'images/sabres-celebration-bruins-game-3-april-23-2026.jpg',
    'knicks-host-sixers-spurs-host-wolves-conference-semis-nba.html': 'images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.webp',
    'eovaldi-warren-ober-mikolas-eleven-game-wednesday-mlb.html': 'images/mlb-bryan-woo-mariners-yankees-pitching.webp'
  };

  var SPORT_FALLBACK_IMAGES = {
    NHL: 'images/sabres-celebration-bruins-game-3-april-23-2026.jpg',
    MLB: 'images/mlb-great-american-ballpark-yankees-reds.webp',
    NBA: 'images/thunderwin.webp',
    NCAAB: 'images/sacramento-kings-oklahoma-city-thunder-nba-over-betting-pick-total-november-19-2025.webp',
    NCAAF: 'images/nfl-ncaaf-two-team-teaser-eagles-tulane-oct-09-2025.webp',
    NFL: 'images/nfl-chiefs-bills-week-9-betting-pick-nov-2-2025.webp',
    Soccer: 'images/soccer-armenia-ireland-corner-betting-oct-14-2025.webp',
    Betting: 'images/mlb-great-american-ballpark-yankees-reds.webp'
  };

  function isLocalImage(src) {
    return typeof src === 'string' && /^images\/[^?#]+?\.(png|jpe?g|webp|gif|svg)$/i.test(src);
  }

  function escapeXml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function wrapLines(text, maxLength) {
    var words = String(text || '').split(/\s+/).filter(Boolean);
    var lines = [];
    var current = '';
    words.forEach(function(word) {
      var next = current ? current + ' ' + word : word;
      if (next.length > maxLength && current) {
        lines.push(current);
        current = word;
      } else {
        current = next;
      }
    });
    if (current) lines.push(current);
    return lines.slice(0, 3);
  }

  function makeThumbnail(meta) {
    var sport = meta && meta.sport ? meta.sport : 'Betting';
    var style = CATEGORY_STYLES[sport] || CATEGORY_STYLES.Betting;
    var badge = meta && meta.badge ? meta.badge : SECTION_LABELS[meta && meta.section ? meta.section : 'pick'] || 'BETLEGEND';
    var titleLines = wrapLines(meta && meta.title ? meta.title : 'BetLegend Picks', 26);
    var kicker = meta && meta.kicker ? meta.kicker : '';
    var titleY = 300;
    var subtitle = kicker ? '<text x="90" y="556" fill="' + style.accent + '" font-family="Inter, Arial, sans-serif" font-size="30" font-weight="500">' + escapeXml(kicker) + '</text>' : '';
    var linesSvg = titleLines.map(function(line, index) {
      return '<text x="90" y="' + (titleY + index * 84) + '" fill="#ffffff" font-family="Inter, Arial, sans-serif" font-size="66" font-weight="800">' + escapeXml(line) + '</text>';
    }).join('');
    var svg = ''
      + '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">'
      + '<defs>'
      + '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
      + '<stop offset="0%" stop-color="' + style.secondary + '"/>'
      + '<stop offset="100%" stop-color="#09090b"/>'
      + '</linearGradient>'
      + '<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
      + '<stop offset="0%" stop-color="' + style.primary + '"/>'
      + '<stop offset="100%" stop-color="' + style.accent + '"/>'
      + '</linearGradient>'
      + '</defs>'
      + '<rect width="1200" height="675" fill="url(#bg)"/>'
      + '<circle cx="1035" cy="140" r="180" fill="' + style.primary + '" opacity="0.16"/>'
      + '<circle cx="1090" cy="535" r="220" fill="' + style.primary + '" opacity="0.12"/>'
      + '<rect x="70" y="74" width="220" height="44" rx="22" fill="url(#accent)"/>'
      + '<text x="180" y="103" text-anchor="middle" fill="#081018" font-family="Inter, Arial, sans-serif" font-size="20" font-weight="800">' + escapeXml(sport.toUpperCase()) + '</text>'
      + '<text x="90" y="170" fill="' + style.accent + '" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="700" letter-spacing="2">' + escapeXml(badge) + '</text>'
      + '<rect x="90" y="196" width="160" height="4" rx="2" fill="' + style.primary + '"/>'
      + linesSvg
      + subtitle
      + '<text x="90" y="620" fill="rgba(255,255,255,0.65)" font-family="Inter, Arial, sans-serif" font-size="24" font-weight="600">BetLegend Picks</text>'
      + '</svg>';
    return 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);
  }

  function resolvePickImage(pick, usedImages) {
    var pickImg = pick && pick.image ? String(pick.image) : '';
    var override = pick && pick.url ? PICK_IMAGE_OVERRIDES[pick.url] : '';
    if (override) {
      if (usedImages) usedImages.add(override);
      return override;
    }
    if (pickImg && pickImg !== 'newlogo.png' && !BLOCKED_IMAGE_RE.test(pickImg)) {
      if (usedImages) usedImages.add(pickImg);
      return pickImg;
    }
    var sport = pick && pick.sport ? pick.sport : 'Betting';
    var src = SPORT_FALLBACK_IMAGES[sport] || SPORT_FALLBACK_IMAGES.Betting;
    if (usedImages) usedImages.add(src);
    return src;
  }

  function resolveStaticImage(card) {
    var key = card && card.key ? card.key : '';
    var category = card && card.category ? card.category : 'Betting';
    var topic = card && card.topic ? card.topic : '';
    var section = card && card.section ? card.section : '';
    var meta = key && STATIC_CARD_META[key] ? STATIC_CARD_META[key] : {
      sport: category,
      title: card && card.title ? card.title : 'BetLegend Picks',
      kicker: topic && TOPIC_LABELS[topic] ? TOPIC_LABELS[topic] : 'Editorial preview card',
      badge: section && SECTION_LABELS[section] ? SECTION_LABELS[section] : 'BETLEGEND'
    };
    if (topic && TOPIC_LABELS[topic] && !STATIC_CARD_META[key]) {
      meta.badge = TOPIC_LABELS[topic];
    }
    return makeThumbnail(meta);
  }

  function normalizeHomepageCardImages(root) {
    var scope = root || document;
    var cards = scope.querySelectorAll('[data-card-key] img[data-card-image]');
    cards.forEach(function(img) {
      var container = img.closest('[data-card-key]');
      if (!container) return;
      var currentSrc = img.getAttribute('src') || '';
      var isPlaceholder = !currentSrc
        || currentSrc === 'newlogo.png'
        || /\/newlogo\.png$/.test(currentSrc)
        || BLOCKED_IMAGE_RE.test(currentSrc);
      if (!isPlaceholder) return;
      img.src = resolveStaticImage({
        key: container.getAttribute('data-card-key'),
        category: container.getAttribute('data-card-category'),
        topic: container.getAttribute('data-card-topic'),
        section: container.getAttribute('data-card-section'),
        src: currentSrc
      });
    });
  }

  window.BetLegendImages = {
    isLocalImage: isLocalImage,
    escapeXml: escapeXml,
    makeThumbnail: makeThumbnail,
    resolvePickImage: resolvePickImage,
    resolveStaticImage: resolveStaticImage,
    normalizeHomepageCardImages: normalizeHomepageCardImages,
    categoryStyles: CATEGORY_STYLES,
    topicLabels: TOPIC_LABELS,
    sectionLabels: SECTION_LABELS,
    staticCardMeta: STATIC_CARD_META,
    blockedImageRe: BLOCKED_IMAGE_RE
  };
})();
