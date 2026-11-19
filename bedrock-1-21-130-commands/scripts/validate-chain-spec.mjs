#!/usr/bin/env node
/**
 * Validate a declarative pure command-block chain spec.
 * Usage: node validate-chain-spec.mjs <spec.json> [--write <plan.md>] [--quiet]
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const commandValidator = path.join(scriptDir, 'validate-commands.mjs');
const args = process.argv.slice(2);
const quiet = args.includes('--quiet');
const writeIndex = args.indexOf('--write');
const writePath = writeIndex >= 0 ? args[writeIndex + 1] : null;
const positional = [];
for (let index = 0; index < args.length; index++) {
  if (args[index] === '--write') {
    index++;
  } else if (!args[index].startsWith('--')) {
    positional.push(args[index]);
  }
}
const file = positional[0];

if (!file || (writeIndex >= 0 && !writePath)) {
  console.error('用法: node validate-chain-spec.mjs <spec.json> [--write <plan.md>] [--quiet]');
  process.exit(2);
}

const absolutePath = path.resolve(file);
if (!fs.existsSync(absolutePath)) {
  console.error(`找不到文件: ${absolutePath}`);
  process.exit(2);
}

const errors = [];
const warnings = [];
const BLOCK_TYPES = new Set(['impulse', 'repeat', 'chain']);
const CONDITIONS = new Set(['unconditional', 'conditional']);
const REDSTONE = new Set(['always_active', 'needs_redstone']);
const FACING = new Set(['north', 'south', 'east', 'west', 'up', 'down']);
const PROJECTION_AXES = new Set(['x', 'z']);
const PROJECTION_LAYOUTS = new Set(['line', 'serpentine']);
const PROJECTION_KEYS = new Set(['origin', 'axis', 'layout', 'width', 'worldName', 'spawn', 'buttons']);
const UNVERIFIED_NETEASE = new Set([
  'camera',
  'inputpermission',
  'dialogue',
  'loot',
  'place',
  'recipe',
  'scriptevent',
  'titleraw',
  'damage',
  'hud'
]);
const FUNCTION_BOUND = new Set(['function', 'schedule', 'reload']);
const ID_RE = /^[A-Za-z][A-Za-z0-9_-]{0,31}$/;
const NAME_RE = /^[a-z][a-z0-9_-]{1,63}$/;

function error(code, message, blockId = null) {
  errors.push({ code, message, blockId });
}

function warn(code, message, blockId = null) {
  warnings.push({ code, message, blockId });
}

function isString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function isStringArray(value) {
  return Array.isArray(value) && value.every(item => typeof item === 'string');
}

function commandName(command) {
  return command.trim().replace(/^\/+/, '').split(/\s+/)[0].toLowerCase();
}

function nestedRunNames(command) {
  const out = [];
  const words = command.split(/\s+/);
  for (let index = 0; index < words.length - 1; index++) {
    if (words[index].toLowerCase() === 'run') out.push(words[index + 1].toLowerCase());
  }
  return out;
}

function checkNetEaseCommands(command, blockId, channel) {
  if (channel !== 'netease-china') return;
  const first = commandName(command);
  const names = first === 'execute' ? [first, ...nestedRunNames(command)] : [first];
  for (const name of names) {
    if (name === 'fog') {
      error('NETEASE_FOG', '网易官方页面标注 fog 当前中国版尚未实装', blockId);
    } else if (UNVERIFIED_NETEASE.has(name)) {
      warn('NETEASE_UNVERIFIED', `/${name} 在网易 1.21.130 默认未验证；先 /help ${name} 或在目标客户端实测`, blockId);
    }
    if (FUNCTION_BOUND.has(name)) {
      error('PURE_FUNCTION_DEPENDENCY', `/${name} 依赖函数或资源重载，不能替代当前纯命令方块链`, blockId);
    }
  }
}

function checkBroadEntity(command, blockId) {
  for (const match of command.matchAll(/@e(?:\[([^\]]*)\])?/gi)) {
    const body = match[1] || '';
    if (!/\btype=|\btag=|\br=|\bx=|@|\bc=/i.test(body)) {
      warn('BROAD_SELECTOR', '裸 @e 可能扫描全部已加载实体；增加 type/tag/区域/c 限制', blockId);
    }
  }
}

function directionDelta(from, to) {
  return [to[0] - from[0], to[1] - from[1], to[2] - from[2]];
}

const expectedDelta = {
  north: [0, 0, -1],
  south: [0, 0, 1],
  east: [1, 0, 0],
  west: [-1, 0, 0],
  up: [0, 1, 0],
  down: [0, -1, 0]
};

function equalTriple(a, b) {
  return a.length === 3 && b.length === 3 && a.every((value, index) => value === b[index]);
}

let spec;
try {
  spec = JSON.parse(fs.readFileSync(absolutePath, 'utf8').replace(/^\uFEFF/, ''));
} catch (failure) {
  console.error(`JSON 解析失败: ${failure.message}`);
  process.exit(2);
}

if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
  console.error('spec 顶层必须是 JSON 对象');
  process.exit(2);
}

if (!isString(spec.name) || !NAME_RE.test(spec.name)) {
  error('SPEC_NAME', 'name 必须是 2–64 位小写字母、数字、下划线或短横线');
}
const channel = spec.channel || 'netease-china';
if (!['netease-china', 'international'].includes(channel)) {
  error('SPEC_CHANNEL', 'channel 只能是 netease-china 或 international');
}
if ((spec.targetVersion || '1.21.130') !== '1.21.130') {
  error('SPEC_VERSION', 'targetVersion 当前必须为 1.21.130');
}
if ((spec.commandsOnly ?? true) !== true) {
  error('SPEC_COMMANDS_ONLY', 'commandsOnly 必须为 true；本 spec 面向纯命令方块');
}
for (const field of ['setup', 'tests', 'notes']) {
  if (spec[field] !== undefined && !isStringArray(spec[field])) {
    error(`SPEC_${field.toUpperCase()}`, `${field} 必须是字符串数组`);
  }
}
if (spec.projection !== undefined) {
  const projection = spec.projection;
  if (!projection || typeof projection !== 'object' || Array.isArray(projection)) {
    error('PROJECTION_OBJECT', 'projection 必须是对象');
  } else {
    for (const key of Object.keys(projection)) {
      if (!PROJECTION_KEYS.has(key)) error('PROJECTION_KEY', `未知 projection 字段: ${key}`);
    }
    for (const field of ['origin', 'spawn']) {
      if (
        projection[field] !== undefined &&
        (!Array.isArray(projection[field]) ||
          projection[field].length !== 3 ||
          !projection[field].every(Number.isInteger))
      ) {
        error('PROJECTION_VECTOR', `projection.${field} 必须是三个整数坐标`);
      }
    }
    if (projection.axis !== undefined && !PROJECTION_AXES.has(projection.axis)) {
      error('PROJECTION_AXIS', 'projection.axis 只能是 x 或 z');
    }
    if (projection.layout !== undefined && !PROJECTION_LAYOUTS.has(projection.layout)) {
      error('PROJECTION_LAYOUT', 'projection.layout 只能是 line 或 serpentine');
    }
    if (
      projection.width !== undefined &&
      (!Number.isInteger(projection.width) || projection.width < 1 || projection.width > 512)
    ) {
      error('PROJECTION_WIDTH', 'projection.width 必须是 1–512 的整数');
    }
    if (projection.worldName !== undefined && !isString(projection.worldName)) {
      error('PROJECTION_WORLD_NAME', 'projection.worldName 必须是非空字符串');
    }
    if (projection.buttons !== undefined && typeof projection.buttons !== 'boolean') {
      error('PROJECTION_BUTTONS', 'projection.buttons 必须是布尔值');
    }
  }
}
if (!Array.isArray(spec.blocks) || spec.blocks.length === 0) {
  error('SPEC_BLOCKS', 'blocks 必须是非空数组');
}

const blocks = Array.isArray(spec.blocks) ? spec.blocks : [];
const positioned = blocks.filter(block => block && Array.isArray(block.pos)).length;
if (positioned > 0 && positioned !== blocks.length) {
  error('MIXED_POSITIONS', '导出投影时，所有 block 要么都写 pos，要么都不写 pos');
}
const byId = new Map();
for (const block of blocks) {
  if (!block || typeof block !== 'object' || Array.isArray(block)) {
    error('BLOCK_OBJECT', '每个 block 必须是对象');
    continue;
  }
  if (!isString(block.id) || !ID_RE.test(block.id)) {
    error('BLOCK_ID', 'block.id 必须是 1–32 位字母开头标识符', block.id || null);
    continue;
  }
  if (byId.has(block.id)) error('BLOCK_ID_DUP', `重复 block.id: ${block.id}`, block.id);
  else byId.set(block.id, block);
}

for (const block of blocks) {
  if (!block || typeof block !== 'object' || !isString(block.id)) continue;
  const id = block.id;
  if (!BLOCK_TYPES.has(block.type)) error('BLOCK_TYPE', 'type 必须是 impulse/repeat/chain', id);
  if (block.condition !== undefined && !CONDITIONS.has(block.condition)) {
    error('BLOCK_CONDITION', 'condition 必须是 unconditional/conditional', id);
  }
  if (block.redstone !== undefined && !REDSTONE.has(block.redstone)) {
    error('BLOCK_REDSTONE', 'redstone 必须是 always_active/needs_redstone', id);
  }
  if (block.delay !== undefined && (!Number.isInteger(block.delay) || block.delay < 0 || block.delay > 65535)) {
    error('BLOCK_DELAY', 'delay 必须是 0–65535 的整数', id);
  }
  if (block.executeFirstTick !== undefined && typeof block.executeFirstTick !== 'boolean') {
    error('BLOCK_FIRST_TICK', 'executeFirstTick 必须是布尔值', id);
  }
  if (block.executeFirstTick !== undefined && block.type !== 'repeat') {
    warn('FIRST_TICK_NON_REPEAT', 'executeFirstTick 只对 repeat 方块有意义', id);
  }
  if (!isString(block.command)) {
    error('BLOCK_COMMAND', 'command 必须是非空字符串', id);
    continue;
  }
  const command = block.command.trim().replace(/^\/+/, '');
  if (command.length > 32500) error('COMMAND_TOO_LONG', 'command 超过约 32,500 字符', id);
  if (block.next !== undefined && block.next !== null && !isString(block.next)) {
    error('BLOCK_NEXT', 'next 必须是 block id 或 null', id);
  }
  if (block.pos !== undefined) {
    if (!Array.isArray(block.pos) || block.pos.length !== 3 || !block.pos.every(Number.isInteger)) {
      error('BLOCK_POS', 'pos 必须是三个整数坐标', id);
    }
  }
  if (block.facing !== undefined && !FACING.has(block.facing)) {
    error('BLOCK_FACING', 'facing 必须是 north/south/east/west/up/down', id);
  }
  if (block.note !== undefined && typeof block.note !== 'string') {
    error('BLOCK_NOTE', 'note 必须是字符串', id);
  }

  checkNetEaseCommands(command, id, channel);
  checkBroadEntity(command, id);

  if (block.type === 'repeat') {
    if (block.redstone === undefined) {
      warn('REPEAT_REDSTONE_DEFAULT', 'repeat 未写 redstone，按 needs_redstone 处理；持续链通常显式写 always_active', id);
    }
    if (block.redstone === 'needs_redstone') {
      warn('REPEAT_REDSTONE', '红石循环不能稳定达到 20 Hz；需要每 tick 时使用 always_active', id);
    }
    if (/\b(?:gamerule|tickingarea\s+add|scoreboard\s+objectives\s+add)\b/i.test(command)) {
      error('ONE_TIME_IN_REPEAT', '一次性初始化命令不能放入 repeat 根', id);
    }
    if (/\b(?:fill|clone|structure\s+load)\b/i.test(command)) {
      warn('EXPENSIVE_IN_REPEAT', 'repeat 根包含区域或结构操作；先用状态门降频', id);
    }
  }
}

const predecessors = new Map(blocks.filter(block => isString(block.id)).map(block => [block.id, []]));
for (const block of blocks) {
  if (!block || !isString(block.id) || !isString(block.next)) continue;
  if (!byId.has(block.next)) {
    error('NEXT_MISSING', `next 引用了不存在的 block: ${block.next}`, block.id);
    continue;
  }
  if (byId.get(block.next)?.type !== 'chain') {
    error('NEXT_NOT_CHAIN', 'next 目标必须是 chain 方块；新链请使用新的 impulse/repeat 根', block.id);
  }
  if (block.next === block.id) {
    error('SELF_LOOP', 'block 不能指向自己', block.id);
    continue;
  }
  predecessors.get(block.next)?.push(block.id);
}

for (const [id, incoming] of predecessors) {
  if (incoming.length > 1) {
    error('MULTIPLE_PREDECESSORS', `block 有多个上游: ${incoming.join(', ')}`, id);
  }
  const block = byId.get(id);
  if (block?.type === 'chain' && incoming.length === 0) {
    error('ORPHAN_CHAIN', 'chain 方块必须有上游；另建 impulse/repeat 链头', id);
  }
  if (block?.type !== 'chain' && incoming.length > 0) {
    error('UPSTREAM_ON_ROOT', 'impulse/repeat 根通常不应有上游；拆成独立链', id);
  }
  if (block?.condition === 'conditional' && incoming.length === 0) {
    error('CONDITIONAL_ROOT', 'conditional 方块必须有紧邻上游', id);
  }
}

for (const block of blocks) {
  if (!block || !isString(block.id) || !isString(block.next)) continue;
  const next = byId.get(block.next);
  if (!next) continue;
  if (Array.isArray(block.pos) && Array.isArray(next.pos) && block.facing) {
    const delta = directionDelta(block.pos, next.pos);
    if (!equalTriple(delta, expectedDelta[block.facing])) {
      error(
        'FACING_MISMATCH',
        `facing=${block.facing} 与下一块坐标差 ${delta.join(',')} 不一致`,
        block.id
      );
    }
  }
  if (next.condition === 'conditional' && Array.isArray(block.pos) && Array.isArray(next.pos)) {
    const delta = directionDelta(block.pos, next.pos);
    if (block.facing && !equalTriple(delta, expectedDelta[block.facing])) {
      error('CONDITIONAL_BEHIND', 'conditional 方块没有紧邻在检查对象的前方', next.id);
    }
  }
}

const roots = blocks.filter(block => isString(block.id) && predecessors.get(block.id)?.length === 0);
if (roots.length === 0) error('NO_ROOT', '至少需要一个 impulse 或 repeat 链头');
for (const root of roots) {
  if (root?.type === 'chain') error('CHAIN_AS_ROOT', 'chain 不能作为链头', root.id);
}

const visitState = new Map();
function visit(id, stack = []) {
  if (visitState.get(id) === 'done') return;
  if (visitState.get(id) === 'active') {
    warn('GRAPH_CYCLE', `检测到环: ${[...stack, id].join(' -> ')}；命令方块环同 tick 每格最多执行一次`, id);
    return;
  }
  visitState.set(id, 'active');
  const next = byId.get(id)?.next;
  if (isString(next) && byId.has(next)) visit(next, [...stack, id]);
  visitState.set(id, 'done');
}
for (const root of roots) visit(root.id);
for (const block of blocks) {
  if (isString(block.id) && !visitState.has(block.id)) {
    warn('UNREACHABLE_BLOCK', 'block 不在任何链头可达的分支中', block.id);
  }
}

if (Array.isArray(spec.setup) || Array.isArray(spec.blocks)) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bedrock-spec-'));
  const commandsFile = path.join(tempDir, 'commands.txt');
  const commands = [
    ...(Array.isArray(spec.setup) ? spec.setup : []),
    ...blocks.filter(block => isString(block?.command)).map(block => block.command)
  ];
  fs.writeFileSync(commandsFile, commands.join('\n') + '\n', 'utf8');
  const validatorChannel = channel === 'international' ? 'international' : 'netease';
  const result = spawnSync(process.execPath, [commandValidator, commandsFile, '--channel', validatorChannel, '--quiet'], {
    encoding: 'utf8'
  });
  if (result.status !== 0) {
    error('COMMAND_VALIDATION', 'setup 或 block command 未通过 validate-commands.mjs');
  }
  fs.rmSync(tempDir, { recursive: true, force: true });
}

function orderedBlocks() {
  const output = [];
  const seen = new Set();
  function walk(id) {
    if (!isString(id) || seen.has(id) || !byId.has(id)) return;
    seen.add(id);
    const block = byId.get(id);
    output.push(block);
    walk(block.next);
  }
  for (const root of roots) walk(root.id);
  for (const block of blocks) walk(block?.id);
  return output;
}

function markdownPlan() {
  const ordered = orderedBlocks();
  const lines = [
    `# ${spec.name || 'Command-block chain'}`,
    '',
    spec.description || '',
    '',
    `- Channel: ${channel}`,
    `- Target: ${spec.targetVersion || '1.21.130'}`,
    `- Blocks: ${ordered.length}`,
    '',
  ];
  if (spec.projection && typeof spec.projection === 'object') {
    const projection = spec.projection;
    lines.push(
      '## Projection',
      '',
      `- Origin: ${(projection.origin || [0, 4, 0]).join(' ')}`,
      `- Layout: ${projection.layout || 'serpentine'}`,
      `- Axis: ${projection.axis || 'x'}`,
      `- Width: ${projection.width ?? 64}`,
      `- Spawn: ${(projection.spawn || []).join(' ') || '(automatic)'}`,
      `- Buttons: ${projection.buttons ?? true}`,
      ''
    );
  }
  lines.push(
    '## Setup',
    '',
    '```text',
    ...((Array.isArray(spec.setup) && spec.setup.length) ? spec.setup.map(command => `/${command.replace(/^\/+/, '')}`) : ['(none)']),
    '```',
    '',
    '## Build table',
    '',
    '| # | Type | Condition | Redstone | Delay | Command | Next | Note |',
    '| --- | --- | --- | --- | ---: | --- | --- | --- |',
    ...ordered.map((block, index) => {
      const condition = block.condition || 'unconditional';
      const redstone = block.redstone || (block.type === 'chain' ? 'always_active' : 'needs_redstone');
      const delay = block.delay ?? 0;
      const command = String(block.command || '').replace(/\|/g, '\\|');
      const note = String(block.note || '').replace(/\|/g, '\\|');
      return `| ${index + 1} | ${block.id} ${block.type} | ${condition} | ${redstone} | ${delay} | \`/${command.replace(/^\/+/, '')}\` | ${block.next || '—'} | ${note} |`;
    }),
    '',
    '## Tests',
    '',
    ...((Array.isArray(spec.tests) && spec.tests.length) ? spec.tests.map(test => `- ${test}`) : ['- Add manual tests before deployment.']),
    '',
    'Static validation only; target-client execution is still required.'
  );
  return lines.join('\n') + '\n';
}

if (!quiet) {
  console.log(`\nSpec: ${absolutePath}`);
  console.log(`Chain: ${spec.name || '(unnamed)'}`);
  console.log(`Channel: ${channel}, blocks: ${blocks.length}`);
  for (const issue of warnings) {
    console.log(`\n  ⚠ ${issue.code}${issue.blockId ? ` [${issue.blockId}]` : ''}: ${issue.message}`);
  }
  for (const issue of errors) {
    console.log(`\n  ✖ ${issue.code}${issue.blockId ? ` [${issue.blockId}]` : ''}: ${issue.message}`);
  }
}

if (errors.length === 0 && writePath) {
  const output = path.resolve(writePath);
  fs.writeFileSync(output, markdownPlan(), 'utf8');
  if (!quiet) console.log(`\n构建表: ${output}`);
}

if (!quiet) {
  if (errors.length === 0) console.log(`\n通过: ${warnings.length} 个警告，0 个错误。`);
  else console.log(`\n结果: ${errors.length} 个错误，${warnings.length} 个警告。`);
}

process.exit(errors.length ? 1 : 0);
