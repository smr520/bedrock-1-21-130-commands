#!/usr/bin/env node
/**
 * 检查命令方块链的结构、多人选择和高频显示风险。
 * 用法: node validate-chains.mjs <文件.md...> [--strict] [--quiet]
 */

import fs from 'node:fs';
import path from 'node:path';

const strict = process.argv.includes('--strict');
const quiet = process.argv.includes('--quiet');
const files = process.argv.slice(2).filter(arg => !arg.startsWith('--'));
const notationRe = /^([A-Za-z]*\d+)\u3010([^\u3011]+)\u3011$/;
const OPEN = '\u3010';
const CLOSE = '\u3011';
const SEP = '\uff5c';

const errors = [];
const warnings = [];

function add(target, file, line, message, command = '') {
  target.push({ file, line, message, command });
}

function nextCommand(lines, start) {
  for (let index = start + 1; index < lines.length; index++) {
    const text = lines[index].trim();
    if (text) return { index, text };
  }
  return null;
}

function parseFile(file) {
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split(/\r?\n/);
  const blocks = [];
  const sections = [];
  let inFence = false;
  let fenceIndex = -1;
  let section = '(root)';

  lines.forEach((raw, index) => {
    const line = index + 1;
    const trimmed = raw.trim();
    if (trimmed.startsWith('```')) {
      if (!inFence) fenceIndex++;
      inFence = !inFence;
      return;
    }
    if (!inFence && /^#{1,6}\s+/.test(trimmed)) {
      section = trimmed.replace(/^#{1,6}\s+/, '');
      return;
    }
    if (!inFence) return;

    const match = trimmed.match(notationRe);
    if (!match) return;
    const settings = match[2].split(SEP).map(part => part.trim()).filter(Boolean);
    const command = nextCommand(lines, index);
    if (!command || !command.text.startsWith('/')) {
      add(errors, file, line, `${match[1]} 后没有可解析的命令`);
      return;
    }
    blocks.push({
      file,
      line,
      id: match[1],
      settings,
      type: settings[0] || '',
      condition: settings[1] || '',
      redstone: settings[2] || '',
      delay: settings[3] || '',
      command: command.text.replace(/^\/+/, ''),
      fenceIndex,
      section
    });
    sections.push({ line, section, fenceIndex });
  });

  return { text, blocks };
}

function validateSequence(block, previous) {
  if (!previous) {
    if (!['循环', '脉冲'].includes(block.type)) {
      add(errors, block.file, block.line, `${block.id} 是链的第一格，但类型不是循环或脉冲`);
    }
    if (block.type === '循环' && block.redstone !== '保持开启') {
      add(warnings, block.file, block.line, `${block.id} 是循环根，当前不是“保持开启”`, block.command);
    }
    if (block.type === '脉冲' && block.redstone !== '需要红石') {
      add(warnings, block.file, block.line, `${block.id} 是脉冲根，当前不是“需要红石”`, block.command);
    }
    return;
  }

  if (block.type !== '连锁') {
    add(errors, block.file, block.line, `${block.id} 与 ${previous.id} 同组，但不是连锁方块`, block.command);
  }
  if (block.settings.length === 4 && previous.settings.length === 4) {
    const sameControl = block.type === '连锁';
    if (sameControl && block.redstone !== '保持开启') {
      add(warnings, block.file, block.line, `${block.id} 是连锁方块，当前不是“保持开启”`, block.command);
    }
  }
}

function validateCommands(block) {
  const oneTime = /\b(?:gamerule|tickingarea\s+add)\b|scoreboard\s+objectives\s+add/i;
  if (block.type === '循环' && oneTime.test(block.command)) {
    add(errors, block.file, block.line, `${block.id} 是循环根，却在重复执行初始化命令`, block.command);
  }
  if (block.type === '循环' && /\b(?:fill|clone)\b/i.test(block.command)) {
    add(warnings, block.file, block.line, `${block.id} 每轮都可能执行大范围方块操作，需确认扫描体积与延迟`, block.command);
  }
  if (block.type === '循环' && /@e(?:\[[^\]]*\])?/.test(block.command)) {
    const selectors = block.command.match(/@e\[[^\]]*\]/g) || ['@e'];
    if (selectors.some(selector => !/\btype=/.test(selector))) {
      add(warnings, block.file, block.line, `${block.id} 每刻扫描 @e 时没有 type=，可能包含大量实体`, block.command);
    }
  }
}

function validateGroup(blocks) {
  let previous = null;
  for (const block of blocks) {
    validateSequence(block, previous);
    validateCommands(block);
    previous = block;
  }

  const repeatedNearest = blocks.filter(block => /@p(?:\[|(?:\s|$))/.test(block.command)).length;
  const hasTagLock = blocks.some(block => /\btag\b[^\n]*\badd\s+[A-Za-z0-9_.:-]+/.test(block.command));
  const hasTransactionMutation = blocks.some(block =>
    /\b(?:clear|give|tp|teleport|scoreboard\s+players\s+(?:add|remove|set))\b/.test(block.command)
  );
  if (repeatedNearest >= 2 && hasTransactionMutation && !hasTagLock) {
    add(
      warnings,
      blocks[0].file,
      blocks[0].line,
      `${blocks[0].id} 所在链多次重新选择 @p；多人共用时可能把交易拆给不同玩家`,
      blocks.map(block => block.command).join(' | ')
    );
  }
}

function validateFile(file) {
  const { text, blocks } = parseFile(file);
  const groups = new Map();
  for (const block of blocks) {
    const prefix = block.id.replace(/\d+$/, '');
    const key = `${block.fenceIndex}:${prefix}:${block.section}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(block);
  }
  for (const group of groups.values()) validateGroup(group);

  const added = new Set();
  const removed = new Set();
  const tagRe = /\btag\b[^\n]*\b(add|remove)\s+([A-Za-z0-9_.:-]+)/g;
  for (const match of text.matchAll(tagRe)) {
    if (match[1] === 'add') added.add(match[2]);
    else removed.add(match[2]);
  }
  for (const tag of added) {
    if (/^(?:tx_|select_|menu_|cb_|damage_|heal_)/.test(tag) && !removed.has(tag)) {
      add(warnings, file, 0, `临时标签 ${tag} 只有 add，没有找到 remove`);
    }
  }

  const actionbarLoops = blocks.filter(block =>
    block.type === '循环' && /\btitleraw\b[^\n]*\bactionbar\b/.test(block.command)
  );
  if (actionbarLoops.length > 1) {
    add(
      warnings,
      file,
      actionbarLoops[1].line,
      '同一文件内有多个循环动作栏输出，可能互相覆盖',
      actionbarLoops.map(block => block.id).join(', ')
    );
  }
}

if (!files.length) {
  console.error('用法: node validate-chains.mjs <文件.md...> [--strict] [--quiet]');
  process.exit(2);
}

for (const file of files) {
  const absolute = path.resolve(file);
  if (!fs.existsSync(absolute)) {
    add(errors, file, 0, '文件不存在');
    continue;
  }
  validateFile(absolute);
}

if (!quiet) {
  for (const item of errors) {
    console.error(`✖ ${item.file}${item.line ? `:L${item.line}` : ''}: ${item.message}`);
  }
  for (const item of warnings) {
    console.warn(`⚠ ${item.file}${item.line ? `:L${item.line}` : ''}: ${item.message}`);
  }
  if (!errors.length && !warnings.length) console.log('通过: 未发现链级结构风险。');
}

process.exit(errors.length || (strict && warnings.length) ? 1 : 0);
