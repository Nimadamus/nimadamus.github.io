// Homepage image resolver for visible cards and pick archive cards.
// Keep this file deterministic: no remote images, no random fallbacks.
(function() {
  var IMAGE_POOLS = {
    NHL: [
      'images/blackhawks-plus-1-5-maple-leafs-december-16-2025.jpeg',
      'images/utah-mammoth-vegas.png',
      'images/bruins-islanders-under-6-nhl-betting-pick-november-26-2025.png',
      'images/dallas-stars-edmonton-oilers-over-6-nhl-betting-pick-november-25-2025.png',
      'images/wild-puck-line-oilers-december-2-2025.png',
      'images/dallas-stars-team-total-under-minnesota-wild-december-11-2025.png',
      'images/sharks-mammoth-nhl-picks-december-1-2025.png',
      'images/anaheim-ducks-nhl-betting-pick-november-19-2025.jpg',
      'images/blackhawks-blues-december-12-2025.jpg',
      'images/blackhawks-puck-line-kings-december-4-2025.png',
      'images/boston-bruins-carolina-hurricanes-nhl-betting-pick-november-17-2025.png',
      'images/devils-team-total-under-dallas-december-3-2025.png',
      'images/islanders-nhl-puck-line-betting-pick-nov-10-2025.png',
      'images/islanders-puck-line-lightning-december-6-2025.png',
      'images/kings-stars-under-5-5-nhl-december-15-2025.jpeg',
      'images/los-angeles-kings-ml-utah-mammoth-december-8-2025.png',
      'images/montreal-canadiens-puck-line-rangers-december-13-2025.jpg',
      'images/penguins-plus-1-5-senators-december-18-2025.png',
      'images/sharks-flames-nhl-puck-line-nov-13-2025.png',
      'images/sharksbruins.png',
      'images/utah-hockey-club-san-jose-sharks-nhl-betting-pick-prediction-november-18-2025.png',
      'images/nhl-avalanche-utah-road-matchup-oct-21-2025.png',
      'images/nhl-oct19.png',
      'images/nhl.png'
    ],
    MLB: [
      'images/mlb-rangers-athletics-prediction-july.png',
      'images/mlb-aaron-judge-yankees-batting.png',
      'images/mlb-twins-coors-field-betting-pick.png',
      'images/mlb-logan-webb-giants-guardians-moneyline.png',
      'images/mlb-world-series-game1-dodgers-betting-pick-oct-24-2025.png',
      'images/mlb-great-american-ballpark-yankees-reds.png',
      'images/mlb-braves-rays-betting-pick-july.png',
      'images/mlb-seattle-mariners-twins-betting-pick.png',
      'images/mlb-red-sox-blue-jays-betting-pick.png',
      'images/mlb-colorado-rockies-brewers-betting-pick.png',
      'images/mlb-giants-dodgers-oracle-park-under-sept-13-2025.png',
      'images/mlb-guardians-moneyline-pick-sept-19-2025.png',
      'images/mlb-cubs-pirates-betting-pick-sept-17-2025.png',
      'images/mlb-garrett-crochet-fenway-park-sept-02-2025.png',
      'images/mlb-yankees-bluejays-alds-game4-total-oct-08-2025.png',
      'images/mlb-picks-team-logos-july-11-2025.png',
      'images/mlb-coors-field-diamondbacks-rockies-over.png',
      'images/mlb-playoffs-pick-oct-01-2025.png'
    ],
    NBA: [
      'images/warriors-kings-kuminga-over-nov5-2025.png',
      'images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.png',
      'images/sacramento-kings-oklahoma-city-thunder-nba-over-betting-pick-total-november-19-2025.png',
      'images/thunderwin.png',
      'images/allstars.png',
      'images/draymond-green-steve-kerr-argument-warriors-dec-23-2025.jpg',
      'images/sac.png'
    ],
    NCAAB: [
      'images/collegeban.png',
      'images/ncaa.png',
      'images/kansas-state-bowling-green-1h-under-76-ncaab-december-2025.png'
    ],
    NCAAF: [
      'images/collegeban.png',
      'images/ncaaf-vanderbilt-lsu-betting-pick-oct-18-2025.png',
      'images/penn-state-ohio-state-ncaaf-betting-pick-nov1-2025.png'
    ],
    Soccer: [
      'images/fifa.png',
      'images/soccer-armenia-ireland-corner-betting-oct-14-2025.png',
      'images/ucl-olympiakos-psv-nov4-2025.png'
    ],
    Betting: [
      'images/proof-bet-screenshot-1000079685.jpg',
      'images/proof-bet-screenshot-1000079686.jpg',
      'images/fantasy-betting-post.png',
      'images/ai-moneyball.png',
      'images/LIVE.png'
    ]
  };

  var KEYWORD_IMAGES = [
    [/maple leafs|leafs/i, 'images/blackhawks-plus-1-5-maple-leafs-december-16-2025.jpeg'],
    [/senators/i, 'images/penguins-plus-1-5-senators-december-18-2025.png'],
    [/kraken/i, 'images/utah-hockey-club-san-jose-sharks-nhl-betting-pick-prediction-november-18-2025.png'],
    [/golden knights|vegas|vgk/i, 'images/utah-mammoth-vegas.png'],
    [/wild/i, 'images/wild-puck-line-oilers-december-2-2025.png'],
    [/blues/i, 'images/blackhawks-blues-december-12-2025.jpg'],
    [/mammoth/i, 'images/sharks-mammoth-nhl-picks-december-1-2025.png'],
    [/flames/i, 'images/sharks-flames-nhl-puck-line-nov-13-2025.png'],
    [/bruins/i, 'images/boston-bruins-carolina-hurricanes-nhl-betting-pick-november-17-2025.png'],
    [/kings/i, 'images/kings-stars-under-5-5-nhl-december-15-2025.jpeg'],
    [/rangers|athletics/i, 'images/mlb-rangers-athletics-prediction-july.png'],
    [/yankees/i, 'images/mlb-aaron-judge-yankees-batting.png'],
    [/dodgers/i, 'images/mlb-world-series-game1-dodgers-betting-pick-oct-24-2025.png'],
    [/giants/i, 'images/mlb-logan-webb-giants-guardians-moneyline.png'],
    [/braves/i, 'images/mlb-braves-rays-betting-pick-july.png'],
    [/mariners/i, 'images/mlb-seattle-mariners-twins-betting-pick.png'],
    [/red sox/i, 'images/mlb-red-sox-blue-jays-betting-pick.png'],
    [/brewers/i, 'images/mlb-colorado-rockies-brewers-betting-pick.png'],
    [/\bhawks\b/i, 'images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.png'],
    [/raptors|thunder/i, 'images/thunderwin.png'],
    [/jazz|rockets/i, 'images/sacramento-kings-oklahoma-city-thunder-nba-over-betting-pick-total-november-19-2025.png']
  ];

  var SPORT_WORDS = {
    NHL: /nhl|hockey|leafs|senators|kraken|golden knights|caps|capitals|blue jackets|wild|blues|mammoth|flames|avalanche|ducks|blackhawks|islanders|bruins|devils|panthers|penguins|sharks|canadiens|rangers|red wings|predators|sabres|kings/i,
    MLB: /mlb|baseball|rangers|athletics|yankees|angels|giants|orioles|dodgers|cardinals|nationals|braves|mariners|red sox|padres|twins|royals|brewers|rays|white sox|blue jays|reds/i,
    NBA: /nba|basketball|warriors|clippers|magic|sixers|hawks|rockets|raptors|thunder|jazz/i,
    NCAAB: /ncaab|college basketball|illinois/i,
    NCAAF: /ncaaf|college football|cfp|bowl/i,
    Soccer: /soccer|fifa|ucl|champions league|real madrid|bayern/i
  };

  var BLOCKED_FOR_GENERAL = /arbitrage/i;

  function isLocalImage(src) {
    return typeof src === 'string' && /^images\/[^?#]+?\.(png|jpe?g|webp|gif)$/i.test(src);
  }

  function sportMatchesImage(sport, src) {
    if (!isLocalImage(src)) return false;
    var name = src.toLowerCase();
    if (sport === 'NHL') return /(nhl|hockey|leafs|senators|kraken|knights|mammoth|bruins|islanders|stars|oilers|wild|blues|ducks|blackhawks|devils|kings|canadiens|penguins|sharks|flames|avalanche)/.test(name);
    if (sport === 'MLB') return /(mlb|baseball|yankees|dodgers|rangers|athletics|giants|braves|mariners|red-sox|brewers|cubs|guardians|coors|playoffs)/.test(name);
    if (sport === 'NBA') return /(nba|basketball|warriors|kings|thunder|pistons|nets|draymond|allstars|sac)/.test(name);
    if (sport === 'NCAAB') return /(collegeban|ncaa|ncaab|kansas-state)/.test(name);
    if (sport === 'NCAAF') return /(ncaaf|college|football|penn-state|vanderbilt)/.test(name);
    if (sport === 'Soccer') return /(soccer|fifa|ucl)/.test(name);
    return true;
  }

  function candidateImages(pick) {
    var sport = pick.sport || 'Betting';
    var haystack = [pick.title, pick.url, sport].join(' ');
    var candidates = [];

    KEYWORD_IMAGES.forEach(function(rule) {
      if (rule[0].test(haystack)) candidates.push(rule[1]);
    });

    if (isLocalImage(pick.image) && sportMatchesImage(sport, pick.image)) {
      candidates.push(pick.image);
    }

    (IMAGE_POOLS[sport] || IMAGE_POOLS.Betting).forEach(function(src) {
      candidates.push(src);
    });

    return candidates.filter(function(src, index, arr) {
      return isLocalImage(src) && arr.indexOf(src) === index;
    });
  }

  function resolvePickImage(pick, usedImages) {
    var candidates = candidateImages(pick);
    var sport = pick.sport || 'Betting';
    var chosen = candidates.find(function(src) {
      return sportMatchesImage(sport, src) && (!usedImages || !usedImages.has(src));
    });

    if (!chosen) {
      chosen = candidates.find(function(src) { return sportMatchesImage(sport, src); }) || (IMAGE_POOLS[sport] || IMAGE_POOLS.Betting)[0];
    }

    if (usedImages && chosen) usedImages.add(chosen);
    return chosen;
  }

  function resolveStaticImage(card) {
    var topic = [card.title || '', card.href || '', card.category || ''].join(' ');
    var category = card.category || 'Betting';
    if (BLOCKED_FOR_GENERAL.test(card.src || '') && !/arbitrage/i.test(topic)) {
      return resolvePickImage({ sport: category, title: topic, url: card.href || '', image: '' });
    }
    if (isLocalImage(card.src) && (!SPORT_WORDS[category] || SPORT_WORDS[category].test(topic))) {
      return card.src;
    }
    return resolvePickImage({ sport: category, title: topic, url: card.href || '', image: card.src || '' });
  }

  window.BetLegendImages = {
    isLocalImage: isLocalImage,
    resolvePickImage: resolvePickImage,
    resolveStaticImage: resolveStaticImage,
    sportMatchesImage: sportMatchesImage,
    imagePools: IMAGE_POOLS
  };
})();
