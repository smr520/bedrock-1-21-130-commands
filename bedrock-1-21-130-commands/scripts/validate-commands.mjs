#!/usr/bin/env node
/**
 * 基岩版 1.21.130 纯指令静态检查
 * 用法: node validate-commands.mjs <文件.txt|文件.md> [--channel netease|international] [--quiet]
 */

import fs from 'node:fs';
import path from 'node:path';

const COMMANDS = new Set([
  'execute', 'scoreboard', 'tag', 'give', 'clear', 'replaceitem', 'summon',
  'setblock', 'fill', 'clone', 'tp', 'teleport', 'gamemode', 'effect',
  'enchant', 'xp', 'kill', 'spawnpoint', 'setworldspawn', 'title', 'titleraw',
  'tellraw', 'playsound', 'stopsound', 'particle', 'time', 'weather',
  'difficulty', 'gamerule', 'tickingarea', 'damage', 'ride', 'camera',
  'inputpermission', 'loot', 'structure', 'place', 'function', 'schedule',
  'reload', 'testfor', 'testforblock', 'testforblocks', 'say', 'me', 'list',
  'locate', 'spreadplayers', 'msg', 'tell', 'w', 'dialogue', 'event',
  'mobevent', 'music', 'fog', 'hud', 'camerashake', 'clearspawnpoint',
  'setmaxplayers', 'querytarget', 'playanimation', 'stopsound', 'recipe',
  'scriptevent'
]);

const JAVA_PARAMS = /\b(limit|sort|distance|nbt|team|predicate|advancements?|bossbar|attribute|forceload|datapack|fillbiome)\s*=/i;
const JAVA_COMMANDS = new Set([
  'data', 'team', 'predicate', 'bossbar', 'attribute', 'advancement',
  'forceload', 'datapack', 'fillbiome', 'item', 'function'
]);

const SYNTAX_FULLWIDTH = new Set([
  '～', '＠', '＃', '％', '＆', '＊', '／', '＝', '＋', '－', '＜', '＞', '｜',
  '，', '：', '；', '（', '）', '“', '”'
]);

const DISPLAY_COMMANDS = new Set(['title', 'say', 'me', 'tell', 'msg', 'w']);
const ALLOWED_ITEM_COMPONENTS = new Set([
  'minecraft:can_place_on', 'can_place_on',
  'minecraft:can_destroy', 'can_destroy',
  'minecraft:item_lock', 'item_lock',
  'minecraft:keep_on_death', 'keep_on_death'
]);
const OPERATORS = new Set(['=', '+=', '-=', '*=', '/=', '%=', '<', '>', '><']);
const NETEASE_UNVERIFIED = new Set([
  'camera', 'inputpermission', 'dialogue', 'loot', 'place', 'recipe',
  'scriptevent', 'titleraw', 'damage', 'hud'
]);

const file = process.argv[2];
const quiet = process.argv.includes('--quiet');
const channelIndex = process.argv.indexOf('--channel');
const channel = channelIndex >= 0 ? process.argv[channelIndex + 1] : 'netease';

if (!file || !['netease', 'international'].includes(channel)) {
  console.error('用法: node validate-commands.mjs <文件.txt|文件.md> [--channel netease|international] [--quiet]');
  process.exit(2);
}

const abs = path.resolve(file);
if (!fs.existsSync(abs)) {
  console.error(`找不到文件: ${abs}`);
  process.exit(2);
}

let text = fs.readFileSync(abs, 'utf8');
if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);

if (text.includes('\uFFFD')) {
  // 不作为致命错误，但提示编码问题
}

const lines = text.split(/\r?\n/);
const errors = [];
const warnings = [];

function err(line, msg, cmd) {
  errors.push({ line, msg, cmd });
}
function warn(line, msg, cmd) {
  warnings.push({ line, msg, cmd });
}
function clip(s, n = 170) {
  s = s.replace(/\s+/g, ' ').trim();
  return s.length > n ? s.slice(0, n) + '…' : s;
}

function tokenize(s) {
  const out = [];
  let cur = '';
  let inQuote = false;
  let esc = false;
  for (const ch of s) {
    if (inQuote) {
      cur += ch;
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === '"') inQuote = false;
    } else if (ch === '"') {
      inQuote = true;
      cur += ch;
    } else if (/\s/.test(ch)) {
      if (cur) { out.push(cur); cur = ''; }
    } else {
      cur += ch;
    }
  }
  if (cur) out.push(cur);
  return out;
}

function extractJson(s) {
  const start = s.indexOf('{');
  if (start < 0) return null;
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < s.length; i++) {
    const ch = s[i];
    if (inStr) {
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === '"') inStr = false;
      continue;
    }
    if (ch === '"') inStr = true;
    else if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) return s.slice(start, i + 1);
    }
  }
  return null;
}

function unescapedQuoteCount(s) {
  let n = 0;
  let esc = false;
  for (const ch of s) {
    if (esc) { esc = false; continue; }
    if (ch === '\\') { esc = true; continue; }
    if (ch === '"') n++;
  }
  return n;
}

function braceBalance(s) {
  let d = 0;
  let inStr = false;
  let esc = false;
  for (const ch of s) {
    if (inStr) {
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === '"') inStr = false;
      continue;
    }
    if (ch === '"') inStr = true;
    else if (ch === '{') d++;
    else if (ch === '}') d--;
  }
  return d;
}

function fullWidthHits(s) {
  const hits = [];
  let inStr = false;
  let esc = false;
  for (const ch of s) {
    if (inStr) {
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === '"') inStr = false;
      continue;
    }
    if (ch === '"') { inStr = true; continue; }
    if (SYNTAX_FULLWIDTH.has(ch)) hits.push(ch);
  }
  return hits;
}

function findCommand(s) {
  let t = s.trim();
  t = t.replace(/^[-*>]\s*/, '');
  t = t.replace(/^\d+[.、)]\s*/, '');
  const close = t.indexOf('】');
  if (close >= 0) t = t.slice(close + 1).trim();
  if (!t) return null;
  if (t.startsWith('/')) return t;
  const first = t.split(/\s+/)[0].toLowerCase();
  if (COMMANDS.has(first)) return t;
  return null;
}

function checkNotation(line, raw) {
  const m = raw.match(/【([^】]+)】/);
  if (!m) return;
  const parts = m[1].split(/[｜|]/).map(x => x.trim()).filter(Boolean);
  if (parts.length !== 4) {
    warn(line, '方块标注不是四段（类型｜条件｜红石｜延迟）', raw);
    return;
  }
  const [type, cond, red, delay] = parts;
  if (!/^(循环|连锁|脉冲)$/.test(type)) warn(line, `未知方块类型「${type}」，应为 循环/连锁/脉冲`, raw);
  if (!/^(无条件|有条件)$/.test(cond)) warn(line, `未知条件「${cond}」，应为 无条件/有条件`, raw);
  if (!/^(保持开启|常开|需要红石|红石控制)$/.test(red)) warn(line, `未知红石状态「${red}」，应为 保持开启/需要红石`, raw);
  if (!/^延迟\s*\d+$/.test(delay)) warn(line, `未知延迟「${delay}」，应写成 延迟0、延迟20`, raw);
}

function validateRawtext(line, cmd) {
  const idx = Math.max(cmd.lastIndexOf('tellraw'), cmd.lastIndexOf('titleraw'));
  if (idx < 0) return;
  const sub = cmd.slice(idx);
  const json = extractJson(sub);
  if (!json) {
    err(line, 'tellraw/titleraw 缺少 JSON 对象', cmd);
    return;
  }
  try {
    const obj = JSON.parse(json);
    if (!obj || !Array.isArray(obj.rawtext)) {
      err(line, 'tellraw/titleraw 必须是 {"rawtext":[...]} 结构', cmd);
      return;
    }
    const visit = (node) => {
      if (Array.isArray(node)) {
        for (const item of node) visit(item);
        return;
      }
      if (!node || typeof node !== 'object') return;

      if (typeof node.translate === 'string') {
        const slot = node.translate.match(/^%%(\d+)$/);
        if (slot) {
          const index = Number(slot[1]);
          const args = Array.isArray(node.with)
            ? node.with
            : Array.isArray(node.with?.rawtext)
              ? node.with.rawtext
              : null;
          if (index < 1) {
            err(line, `translate %%${index} 的槽位必须从 %%1 开始`, cmd);
          } else if (!args) {
            err(line, `translate %%${index} 缺少 with 参数列表`, cmd);
          } else if (index > args.length) {
            err(line, `translate %%${index} 需要至少 ${index} 个 with 参数，当前只有 ${args.length} 个`, cmd);
          }
        }
      }

      for (const value of Object.values(node)) visit(value);
    };
    visit(obj.rawtext);
  } catch (e) {
    err(line, `tellraw/titleraw JSON 解析失败: ${e.message}`, cmd);
  }
}

function validateGive(line, cmd) {
  const idx = cmd.lastIndexOf('give');
  if (idx < 0) return;
  const sub = cmd.slice(idx);
  if (!sub.includes('{')) return;
  const json = extractJson(sub);
  if (!json) {
    err(line, 'give 的组件 JSON 不完整', cmd);
    return;
  }
  try {
    const obj = JSON.parse(json);
    for (const key of Object.keys(obj)) {
      if (!ALLOWED_ITEM_COMPONENTS.has(key)) {
        err(line, `give 不支持组件「${key}」；只支持 can_place_on/can_destroy/item_lock/keep_on_death`, cmd);
      }
    }
  } catch {
    err(line, 'give 不能带 Java NBT；只支持 can_place_on/can_destroy/item_lock/keep_on_death 四种组件 JSON', cmd);
  }
}

function validateReplaceitem(line, cmd) {
  const idx = cmd.lastIndexOf('replaceitem');
  const sub = idx >= 0 ? cmd.slice(idx) : cmd;
  const t = tokenize(sub);
  if (t[0] === 'replaceitem') {
    const modeIndex = t[1] === 'entity' ? 5 : t[1] === 'block' ? 7 : -1;
    if (modeIndex >= 0 && !['destroy', 'keep'].includes(t[modeIndex])) {
      warn(line, '1.21.130 推荐在 replaceitem 中显式写旧物品处理方式 destroy 或 keep', cmd);
    }
  }
  if (/\bweapon\.mainhand\b/.test(cmd) && !/slot\.weapon\.mainhand/.test(cmd)) {
    err(line, '基岩版槽位要写 slot.weapon.mainhand 0', cmd);
  }
  if (/\barmor\.(head|chest|legs|feet)\b/.test(cmd) && !/slot\.armor\./.test(cmd)) {
    err(line, '基岩版槽位要写 slot.armor.head 0 这类形式', cmd);
  }
  if (!cmd.includes('{')) return;
  const json = extractJson(cmd);
  if (!json) return;
  try {
    const obj = JSON.parse(json);
    for (const key of Object.keys(obj)) {
      if (!ALLOWED_ITEM_COMPONENTS.has(key)) {
        err(line, `replaceitem 不支持组件「${key}」`, cmd);
      }
    }
  } catch {
    err(line, 'replaceitem 组件只能写 can_place_on/can_destroy/item_lock/keep_on_death 四种 JSON', cmd);
  }
}

function validateScoreboard(line, cmd) {
  const t = tokenize(cmd);
  if (t[0] !== 'scoreboard') return;

  if (t[1] === 'objectives' && t[2] === 'add') {
    if (t.length < 5) {
      err(line, 'scoreboard objectives add 参数不足', cmd);
      return;
    }
    if (t[4] !== 'dummy') {
      err(line, `基岩版只支持 dummy，不能写「${t[4]}」`, cmd);
    }
  }

  if (t[1] === 'objectives' && t[2] === 'setdisplay') {
    const slot = t[3];
    if (slot === 'below_name') {
      err(line, '基岩版槽位是 belowname，不是 below_name', cmd);
    } else if (!['sidebar', 'list', 'belowname'].includes(slot)) {
      warn(line, `未知显示槽「${slot}」，应为 sidebar/list/belowname`, cmd);
    }
  }

  if (t[1] === 'players' && t[2] === 'operation') {
    const op = t[5];
    if (op && !OPERATORS.has(op)) {
      warn(line, `未知运算「${op}」，可用 = += -= *= /= %= < > ><`, cmd);
    }
  }

  const expected = {
    set: [6, 6],
    add: [6, 6],
    remove: [6, 6],
    reset: [4, 5],
    list: [3, 4],
    test: [7, 8],
    random: [7, 7],
    operation: [8, 8]
  }[t[2]];
  if (t[1] === 'players' && expected) {
    const [min, max] = expected;
    if (t.length < min || t.length > max) {
      err(
        line,
        `scoreboard players ${t[2]} 参数数量应为 ${min === max ? min : `${min}–${max}`} 个，实际 ${t.length} 个`,
        cmd
      );
    }
  }

  if (t[1] === 'players' && t[2] === 'test') {
    warn(line, 'scoreboard players test 是旧教程写法；改成 execute if score ... matches ...', cmd);
  }
}

function targetCanMatchMultiple(target) {
  const match = target.match(/^@([aenprs])(?:\[(.*)\])?$/i);
  if (!match) return false;
  const selector = match[1].toLowerCase();
  const body = match[2] || '';
  const count = body.match(/(?:^|,)c=(-?\d+)(?:,|$)/i)?.[1];
  const absoluteCount = count === undefined ? 1 : Math.abs(Number(count));
  if (absoluteCount === 0) return false;

  if (selector === 'a' || selector === 'e') return count === undefined || absoluteCount !== 1;
  if (selector === 'p' || selector === 'r' || selector === 'n') return count !== undefined && absoluteCount > 1;
  return false;
}

function validateScoreComparisons(line, cmd) {
  const tokens = tokenize(cmd);
  for (let index = 0; index < tokens.length - 5; index++) {
    if (!['if', 'unless'].includes(tokens[index]?.toLowerCase()) || tokens[index + 1] !== 'score') continue;
    if (tokens[index + 4] === 'matches') {
      const target = tokens[index + 2];
      if (targetCanMatchMultiple(target)) {
        err(
          line,
          `execute ${tokens[index]} score matches 的目标 ${target} 可能匹配多个实体；目标必须解析为单一实体，请加 c=1 或改用 execute as`,
          cmd
        );
      }
      continue;
    }
    if (!['=', '<', '<=', '>', '>='].includes(tokens[index + 4])) continue;

    for (const target of [tokens[index + 2], tokens[index + 5]]) {
      if (targetCanMatchMultiple(target)) {
        err(
          line,
          `execute ${tokens[index]} score 的比较目标 ${target} 可能匹配多个实体；两侧都必须解析为单一目标，请加 c=1 或改用双重遍历`,
          cmd
        );
      }
    }
  }
}

function validateTeleportDestination(line, cmd) {
  const tokens = tokenize(cmd);
  let index = -1;
  if (['tp', 'teleport'].includes(tokens[0]?.toLowerCase())) {
    index = 0;
  } else {
    const run = tokens.findIndex(token => token.toLowerCase() === 'run');
    if (run >= 0 && ['tp', 'teleport'].includes(tokens[run + 1]?.toLowerCase())) index = run + 1;
  }
  if (index < 0 || tokens.length < index + 3) return;

  const destination = tokens[index + 2];
  if (targetCanMatchMultiple(destination)) {
    err(
      line,
      `tp/teleport 的实体目的地 ${destination} 可能匹配多个实体；目的地必须解析为单一实体，请加 c=1`,
      cmd
    );
  }
}

function isCompleteConditionOnlyExecute(tokens) {
  for (let index = 0; index < tokens.length - 1; index++) {
    if (!['if', 'unless'].includes(tokens[index]?.toLowerCase())) continue;
    const kind = tokens[index + 1]?.toLowerCase();
    const end = tokens.length;

    if (kind === 'block') {
      if (end === index + 6) return true;
      if (end === index + 7 && tokens[index + 6]?.startsWith('[')) return true;
    }
    if (kind === 'blocks') {
      if (end === index + 12 && ['all', 'masked'].includes(tokens[index + 11]?.toLowerCase())) return true;
    }
    if (kind === 'entity' && end === index + 3) return true;
    if (kind === 'score') {
      if (end === index + 6 && tokens[index + 4]?.toLowerCase() === 'matches') return true;
      if (end === index + 7 && ['=', '<', '<=', '>', '>='].includes(tokens[index + 4])) return true;
    }
  }
  return false;
}

function validateBlockData(line, cmd) {
  const t = tokenize(cmd);
  if (t[0] === 'setblock' && t.length >= 6 && /^\d+$/.test(t[5])) {
    warn(line, '1.19.70 起 setblock 不再用数据值；改用方块状态 ["state"=value]', cmd);
  }
  if (t[0] === 'fill' && t.length >= 9 && /^\d+$/.test(t[8])) {
    warn(line, '1.19.70 起 fill 不再用数据值；改用方块状态 ["state"=value]', cmd);
  }
}

function validateVolume(line, cmd) {
  const t = tokenize(cmd);
  if (t[0] === 'fill' && t.length >= 7) {
    const c = t.slice(1, 7);
    if (c.every(x => /^-?\d+$/.test(x))) {
      const [x1, y1, z1, x2, y2, z2] = c.map(Number);
      const v = (Math.abs(x2 - x1) + 1) * (Math.abs(y2 - y1) + 1) * (Math.abs(z2 - z1) + 1);
      if (v > 32768) warn(line, `fill 体积约 ${v}，超过 32768，命令会失败；拆成多层`, cmd);
    }
  }
  if (t[0] === 'clone' && t.length >= 7) {
    const c = t.slice(1, 7);
    if (c.every(x => /^-?\d+$/.test(x))) {
      const [x1, y1, z1, x2, y2, z2] = c.map(Number);
      const v = (Math.abs(x2 - x1) + 1) * (Math.abs(y2 - y1) + 1) * (Math.abs(z2 - z1) + 1);
      if (v > 655360) warn(line, `clone 源区域约 ${v}，超过 655360，命令会失败`, cmd);
    }
  }
}

function commandNames(cmd) {
  const words = tokenize(cmd);
  const names = [];
  if (words[0]) names.push(words[0].toLowerCase());
  if (words[0]?.toLowerCase() !== 'execute') return names;
  for (let index = 0; index < words.length - 1; index++) {
    if (words[index].toLowerCase() === 'run') names.push(words[index + 1].toLowerCase());
  }
  return names;
}

function validateNetEaseBoundary(line, cmd) {
  if (channel !== 'netease') return;
  for (const name of commandNames(cmd)) {
    if (name === 'fog') {
      warn(line, 'fog 的网易官方资料存在冲突；默认不用，先 /help fog 和目标客户端实测', cmd);
    } else if (NETEASE_UNVERIFIED.has(name)) {
      warn(
        line,
        `/${name} 在网易 1.21.130 默认未验证；先 /help ${name} 或在目标客户端实测，并记录证据等级`,
        cmd
      );
    }
  }
}

let commandCount = 0;
let pendingBlockType = '';

lines.forEach((raw, i) => {
  const line = i + 1;
  const notation = raw.match(/【([^】]+)】/);
  if (notation) {
    pendingBlockType = notation[1].split(/[｜|]/)[0]?.trim() || '';
  }
  checkNotation(line, raw);

  const found = findCommand(raw);
  if (!found) return;

  const cmd = found.replace(/^\/+/, '').trim();
  if (!cmd) return;
  const currentBlockType = pendingBlockType;
  pendingBlockType = '';
  commandCount++;

  if (found.length > 32500) {
    err(line, `命令长度 ${found.length}，超过基岩版命令方块约 32,500 字符上限`, found);
  } else if (found.length > 8000) {
    warn(line, `单条命令长度 ${found.length}，复制和维护风险较高；确认是否能用更短的选择器/状态机`, found);
  }

  const first = cmd.split(/\s+/)[0].toLowerCase();

  validateNetEaseBoundary(line, cmd);

  // 旧 execute
  if (/^execute\s+@/.test(cmd)) {
    err(line, '旧 execute 语法；改成 execute as <目标> at @s run <命令>', found);
    return;
  }

  // 动作型 execute 必须有 run；纯条件型必须以完整 if/unless 结尾
  if (first === 'execute') {
    const t = tokenize(cmd);
    if (!t.includes('run') && !isCompleteConditionOnlyExecute(t)) {
      err(line, 'execute 既没有 run，也没有以完整的 if/unless 条件子命令结尾', found);
    }
    if (/\bexecute\s+always\b/i.test(cmd)) {
      err(line, '基岩版没有 execute always；持续执行请使用循环命令方块', found);
    }
    if (/\bexecute\s+if\s+weather\b/i.test(cmd)) {
      err(line, '基岩版不能直接 execute if weather；用机关维护自定义天气状态', found);
    }
  }
  if (/\b(?:if|unless)\s+score\b/i.test(cmd)) validateScoreComparisons(line, cmd);
  validateTeleportDestination(line, cmd);
  if (/\s&&\s/.test(cmd)) {
    err(line, '检测到 && 串联命令；现代命令方块应拆成独立动作并使用普通/有条件连锁', found);
  }

  // Java 参数
  const jm = cmd.match(JAVA_PARAMS);
  if (jm) {
    const what = jm[1];
    const hint = {
      limit: '用 c=数量',
      sort: '用 c= 的距离排序/反向',
      distance: '用 r=/rm=',
      nbt: '基岩版不支持 NBT 选择器；用 tag/分数',
      team: '用 tag',
      predicate: '基岩版不支持 predicate',
      advancement: '基岩版不支持 advancement',
      advancements: '基岩版不支持 advancements',
      bossbar: '用 title/titleraw 或侧边栏',
      attribute: '基岩版不支持 attribute',
      forceload: '用 tickingarea',
      datapack: '用行为包；纯指令不需要',
      fillbiome: '基岩版不支持 fillbiome'
    }[what] || '基岩版不支持';
    err(line, `Java 参数 ${what}= 不可用；${hint}`, found);
  }

  if (/\bexecute\s+store\b/i.test(cmd)) {
    err(line, '基岩版没有 execute store；用 scoreboard players operation', found);
  }
  if (/\bdata\s+(get|merge|modify)\b/i.test(cmd)) {
    err(line, '基岩版没有 data 命令；用记分板/hasitem/结构', found);
  }
  if (/\bif\s+items\b/i.test(cmd)) {
    err(line, '基岩版没有 execute if items；用 hasitem 选择器', found);
  }
  if (/\bexecute\s+if\s+weather\b/i.test(cmd)) {
    err(line, '基岩版没有 execute if weather；原版纯指令不能直接读取当前天气', found);
  }
  if (/\bexecute\s+always\b/i.test(cmd)) {
    err(line, 'Java 的 execute always 不属于基岩版语法；持续执行请使用循环命令方块', found);
  }
  if (/\bif\s+score\s+\S+\s+\S+\s+exists\b/i.test(cmd)) {
    err(line, '基岩版 if score 不支持 exists 后缀；先建立分数，再用 matches 判断', found);
  }
  if (/\bif\s+biome\b/i.test(cmd)) {
    err(line, '基岩版没有 execute if biome', found);
  }
  if (/\bitem\s+replace\b/i.test(cmd)) {
    err(line, '基岩版没有 /item replace；用 /replaceitem', found);
  }
  if (/[\[,]type=#/i.test(cmd)) {
    err(line, '基岩版选择器不支持 type=#实体标签；改用明确 ID 或 tag', found);
  }

  const nested = cmd.match(/\brun\s+([a-z]+)\b/i);
  if (nested && (JAVA_COMMANDS.has(nested[1].toLowerCase()) || ['schedule', 'reload'].includes(nested[1].toLowerCase()))) {
    err(line, `纯命令方块版本不能在 run 后调用 /${nested[1]}；展开动作或改用方块链`, found);
  }

  if (JAVA_COMMANDS.has(first)) {
    if (first === 'function') {
      err(line, '纯命令方块版本不要 /function；把函数内的每条命令展开成方块', found);
    } else if (first === 'item') {
      err(line, '基岩版没有 /item；用 /replaceitem', found);
    } else {
      err(line, `基岩版没有 /${first} 命令`, found);
    }
  }

  if (first === 'testfor' || first === 'testforblock' || first === 'testforblocks') {
    warn(line, `${first} 仍可用，但建议改成 execute if entity/block/blocks`, found);
  }
  if (first === 'scoreboard' && /\bplayers\s+test\b/i.test(cmd)) {
    warn(line, '旧教程常用 scoreboard players test；纯命令方块建议改用 execute if score ... matches', found);
  }
  if (first === 'schedule') {
    err(line, '网易命令表有 /schedule，但它依赖 Add-on 函数；纯命令方块版用分数计时器、方块延迟或独立触发链', found);
  }
  if (first === 'reload') {
    err(line, '纯命令方块版本不要 /reload；修改方块内容后直接保存/重进验证', found);
  }

  if (currentBlockType === '循环') {
    if (first === 'gamerule') {
      err(line, '不要每刻重复设置游戏规则；把 /gamerule 放进独立的初始化按钮链', found);
    }
    if (first === 'scoreboard' && /\bobjectives\s+add\b/i.test(cmd)) {
      err(line, '不要每刻重复创建记分板目标；把 objectives add 放进独立的初始化按钮链', found);
    }
    if (first === 'tickingarea' && /\badd\b/i.test(cmd)) {
      err(line, '不要每刻重复添加常加载区；把 tickingarea add 放进初始化或手动执行一次', found);
    }
  }

  // NBT
  if (first === 'summon' && cmd.includes('{')) {
    err(line, 'summon 不能带 NBT；用生成事件或行为包', found);
  }
  if (first === 'give' || /\brun\s+give\b/.test(cmd)) validateGive(line, found);
  if (first === 'replaceitem' || /\brun\s+replaceitem\b/.test(cmd)) validateReplaceitem(line, found);

  // 文本
  if (/\b(tellraw|titleraw)\b/.test(cmd)) validateRawtext(line, found);
  if (first === 'title' && cmd.includes('{"text"')) {
    warn(line, 'title 用纯文本；要 JSON 请用 titleraw', found);
  }

  // 记分板
  validateScoreboard(line, cmd);

  // 方块数据值 / 体积
  validateBlockData(line, cmd);
  validateVolume(line, cmd);

  // tag 参数
  if (first === 'tag') {
    const t = tokenize(cmd);
    if ((t[2] === 'add' || t[2] === 'remove') && t.length < 4) {
      err(line, 'tag add/remove 缺少标签名', found);
    }
  }

  // 全角符号
  if (!DISPLAY_COMMANDS.has(first)) {
    const hits = fullWidthHits(cmd);
    if (hits.length) {
      err(line, `命令语法里有全角符号 ${[...new Set(hits)].join(' ')}；换成半角`, found);
    }
  }

  // 负号 U+2212
  if (cmd.includes('−')) {
    err(line, '负号用了 U+2212；换成半角 -', found);
  }

  // 引号/括号
  if (unescapedQuoteCount(cmd) % 2 !== 0) {
    err(line, '双引号不成对', found);
  }
  if ((/\b(tellraw|titleraw|give|replaceitem)\b/.test(cmd)) && braceBalance(cmd) !== 0) {
    err(line, '花括号不成对', found);
  }
});

if (text.includes('\uFFFD')) {
  err(0, '文件包含 U+FFFD 替换字符，可能不是有效 UTF-8；先用正确编码重新保存');
}

if (!quiet) {
  console.log(`\n检查: ${abs}`);
  console.log(`行数: ${lines.length}，命令: ${commandCount}`);

  for (const e of errors) {
    console.log(`\n  ✖ L${e.line}: ${e.msg}`);
    if (e.cmd) console.log(`      ${clip(e.cmd)}`);
  }
  for (const w of warnings) {
    console.log(`\n  ⚠ L${w.line}: ${w.msg}`);
    if (w.cmd) console.log(`      ${clip(w.cmd)}`);
  }

  if (!errors.length && !warnings.length) console.log('\n通过：没有发现明显问题。');
  else console.log(`\n结果: ${errors.length} 个错误，${warnings.length} 个警告。`);
}

process.exit(errors.length ? 1 : 0);
