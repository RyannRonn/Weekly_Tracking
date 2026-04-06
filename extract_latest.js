const fs = require('fs');
const html = fs.readFileSync('C:/Users/tjqud/Desktop/TRACKING/Weekly_Tracking/index.html', 'utf-8');

// Extract DATA object
const dataMatch = html.match(/const DATA\s*=\s*(\{[\s\S]*?\});\s*\n\s*const /);
let DATA, AMZN;

if (dataMatch) {
  try {
    DATA = (new Function('return ' + dataMatch[1]))();
  } catch(e) {
    console.error('Failed to parse DATA:', e.message);
  }
}

// Extract AMZN object
const amznMatch = html.match(/const AMZN\s*=\s*(\{[\s\S]*?\});\s*\n/);
if (amznMatch) {
  try {
    AMZN = (new Function('return ' + amznMatch[1]))();
  } catch(e) {
    console.error('Failed to parse AMZN:', e.message);
  }
}

if (!DATA) {
  // Try alternative: eval approach with sandboxing
  const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/g);
  if (scriptMatch) {
    for (const block of scriptMatch) {
      if (block.includes('const DATA')) {
        const code = block.replace(/<\/?script>/g, '');
        // Extract just the assignments
        const dataLine = code.match(/const DATA\s*=\s*(\{.*?\});/s);
        if (dataLine) {
          DATA = (new Function('return ' + dataLine[1]))();
        }
      }
    }
  }
}

// If regex approach fails, try a different extraction
if (!DATA) {
  // Find start of DATA
  const dataStart = html.indexOf('const DATA = {');
  if (dataStart > -1) {
    let braceCount = 0;
    let started = false;
    let startIdx = html.indexOf('{', dataStart);
    let endIdx = startIdx;
    for (let i = startIdx; i < html.length; i++) {
      if (html[i] === '{') { braceCount++; started = true; }
      if (html[i] === '}') { braceCount--; }
      if (started && braceCount === 0) { endIdx = i + 1; break; }
    }
    const dataStr = html.substring(startIdx, endIdx);
    try {
      DATA = (new Function('return ' + dataStr))();
    } catch(e) {
      console.error('Brace-counting parse failed for DATA:', e.message);
    }
  }
}

if (!AMZN) {
  const amznStart = html.indexOf('const AMZN = {');
  if (amznStart > -1) {
    let braceCount = 0;
    let started = false;
    let startIdx = html.indexOf('{', amznStart);
    let endIdx = startIdx;
    for (let i = startIdx; i < html.length; i++) {
      if (html[i] === '{') { braceCount++; started = true; }
      if (html[i] === '}') { braceCount--; }
      if (started && braceCount === 0) { endIdx = i + 1; break; }
    }
    const amznStr = html.substring(startIdx, endIdx);
    try {
      AMZN = (new Function('return ' + amznStr))();
    } catch(e) {
      console.error('Brace-counting parse failed for AMZN:', e.message);
    }
  }
}

const output = {};

// ===== SPOTIFY =====
if (DATA && DATA.spotify) {
  const dates = Object.keys(DATA.spotify).sort();
  const latest = dates[dates.length - 1];
  const prev = dates[dates.length - 2];
  output.spotify = {
    latest_date: latest,
    prev_date: prev,
    total_dates: dates.length,
    latest_data: DATA.spotify[latest],
    prev_data: DATA.spotify[prev]
  };
}

// ===== TIKTOK =====
if (DATA && DATA.tiktok_videos) {
  output.tiktok = {};
  const categories = Object.keys(DATA.tiktok_videos);
  for (const cat of categories) {
    const catData = DATA.tiktok_videos[cat];
    const dates = Object.keys(catData).sort();
    const latest = dates[dates.length - 1];
    const prev = dates[dates.length - 2];

    const latestEntries = catData[latest];
    const tags = Object.keys(latestEntries);

    // Build arrays for sorting
    const items = tags.map(tag => ({
      tag,
      value: latestEntries[tag].value,
      wow: latestEntries[tag].wow,
      delta: prev && catData[prev][tag] ? latestEntries[tag].value - catData[prev][tag].value : null
    }));

    // Top 10 by value
    const topByValue = [...items].sort((a, b) => b.value - a.value).slice(0, 10);
    // Top 10 by delta (순증)
    const topByDelta = [...items].filter(x => x.delta !== null).sort((a, b) => b.delta - a.delta).slice(0, 10);
    // Top 10 by wow%
    const topByWow = [...items].filter(x => x.wow !== null && x.wow !== 0).sort((a, b) => b.wow - a.wow).slice(0, 10);
    // Bottom by wow (biggest drops)
    const bottomByWow = [...items].filter(x => x.wow !== null && x.wow !== 0).sort((a, b) => a.wow - b.wow).slice(0, 5);

    output.tiktok[cat] = {
      latest_date: latest,
      prev_date: prev,
      total_tags: tags.length,
      top10_by_value: topByValue,
      top10_by_delta: topByDelta,
      top10_by_wow_pct: topByWow,
      bottom5_by_wow_pct: bottomByWow
    };
  }
}

// ===== DELTA WEEKLY =====
if (DATA && DATA.delta_weekly) {
  const dates = Object.keys(DATA.delta_weekly).sort();
  const latest = dates[dates.length - 1];
  const prev = dates[dates.length - 2];
  output.delta_weekly = {
    latest_date: latest,
    prev_date: prev,
    latest_data: DATA.delta_weekly[latest],
    prev_data: DATA.delta_weekly[prev]
  };
}

// ===== WEEKLY_DATES =====
if (DATA && DATA.spotify) {
  output.weekly_dates = Object.keys(DATA.spotify).sort();
  output.latest_2_dates = output.weekly_dates.slice(-2);
}

// ===== AMAZON =====
if (AMZN) {
  output.amazon = {};
  const brands = Object.keys(AMZN);
  for (const brand of brands) {
    const brandData = AMZN[brand];
    if (typeof brandData === 'object' && brandData !== null) {
      // Check if it's date-keyed or has nested structure
      const keys = Object.keys(brandData);
      if (keys.length > 0) {
        // Try to find dates
        const sortedKeys = keys.sort();
        const latestKey = sortedKeys[sortedKeys.length - 1];
        const prevKey = sortedKeys[sortedKeys.length - 2];
        output.amazon[brand] = {
          total_entries: keys.length,
          latest_key: latestKey,
          latest_data: brandData[latestKey],
          prev_key: prevKey,
          prev_data: brandData[prevKey]
        };
      }
    }
  }
}

console.log(JSON.stringify(output, null, 2));
