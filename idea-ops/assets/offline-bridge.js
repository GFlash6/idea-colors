/* Local-file handoff. No requests, timers or background process. */
function mergeOfflineIdeas(local, incoming) {
  const result = JSON.parse(JSON.stringify(local));
  const conflicts = [];
  if (!incoming) return {data: result, conflicts, added: 0, updated: 0};
  if (typeof incoming.workspace !== 'string' || incoming.data?.version !== 1 || !Array.isArray(incoming.data.ideas))
    throw new Error('本地交接文件格式不正确');
  const canonical = value => {
    if (Array.isArray(value)) return value.map(canonical);
    if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort()
      .filter(key => !['position','updated_at'].includes(key)).map(key => [key,canonical(value[key])]));
    return value;
  };
  const same = (a,b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
  // ponytail: project-level conflict handling preserves edits and graph integrity.
  // Field-level collaborative merging is deliberately outside this local handoff.
  const baselines = result.offline_baselines ||= [];
  let entry = baselines.find(item => item.workspace === incoming.workspace);
  if (!entry) { entry = {workspace:incoming.workspace, ideas:[]}; baselines.push(entry); }
  let added = 0, updated = 0;
  const seen = new Set();
  for (const remote of incoming.data.ideas) {
    if (!remote || typeof remote.id !== 'string' || !remote.id || seen.has(remote.id) ||
        typeof remote.title !== 'string' || !Array.isArray(remote.logs) || !Array.isArray(remote.relations))
      throw new Error('本地交接文件包含无效或重复想法');
    seen.add(remote.id);
    const index = result.ideas.findIndex(idea => idea.id === remote.id);
    const baseIndex = entry.ideas.findIndex(idea => idea.id === remote.id);
    const base = entry.ideas[baseIndex];
    const current = result.ideas[index];
    if (base && same(remote, base)) continue;
    if (current && same(current, remote)) {
      // Both sides already contain this version; establish the comparison baseline.
    } else if ((!current && !base) || (current && base && same(current, base))) {
      const copy = JSON.parse(JSON.stringify(remote));
      for (const log of copy.logs) {
        const old = current?.logs.find(item => item.id === log.id);
        if (old?.position) log.position = old.position;
      }
      if (index < 0) {result.ideas.push(copy); added++;}
      else {result.ideas[index] = copy; updated++;}
    } else {
      conflicts.push(remote.title);
      continue; // Includes locally deleted projects: never resurrect them silently.
    }
    const copy = JSON.parse(JSON.stringify(remote));
    if (baseIndex < 0) entry.ideas.push(copy); else entry.ideas[baseIndex] = copy;
  }
  return {data:result, conflicts, added, updated};
}
if (typeof module !== 'undefined') module.exports = {mergeOfflineIdeas};
