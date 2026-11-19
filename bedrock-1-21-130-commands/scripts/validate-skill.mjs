#!/usr/bin/env node
/**
 * 校验 skill 的入口、命令示例和声明方块数。
 * 用法: node validate-skill.mjs [--quiet]
 */

import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const quiet = process.argv.includes('--quiet');
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(scriptDir);
const commandValidator = path.join(scriptDir, 'validate-commands.mjs');
const chainValidator = path.join(scriptDir, 'validate-chains.mjs');
const chainSpecValidator = path.join(scriptDir, 'validate-chain-spec.mjs');
const errors = [];

const OPEN = '\u3010';
const CLOSE = '\u3011';
const SEP = '\uff5c';
const notationRe = /^([A-Za-z]*\d+)\u3010([^\u3011]+)\u3011$/;

function fail(file, line, message) {
  errors.push({ file, line, message });
}

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8');
}

function validateFrontmatter() {
  const text = read('SKILL.md');
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!match) {
    fail('SKILL.md', 1, '缺少 YAML frontmatter');
    return;
  }

  const name = match[1].match(/^name:\s*(.+)$/m)?.[1]?.trim();
  const description = match[1].match(/^description:\s*(.+)$/m)?.[1]?.trim();
  if (name !== path.basename(root)) {
    fail('SKILL.md', 1, `frontmatter name 必须与目录名一致：${path.basename(root)}`);
  }
  if (!description) fail('SKILL.md', 1, 'frontmatter 缺少 description');
}

function safeRuntimeFiles() {
  const fixed = [
    'SKILL.md',
    'references/block-budget.md',
    'references/channel-matrix.md',
    'references/command-ui-playbook.md',
    'references/command-model.md',
    'references/command-blocks.md',
    'references/commands.md',
    'references/netease-1.21.130.md',
    'references/projection-export.md',
    'references/selectors-and-scoreboard.md',
    'references/shared-core.md',
    'references/system-ideas.md',
    'references/systems.md',
    'references/test-matrix.md',
    'references/version-1.21.130.md'
  ];
  const examplesDir = path.join(root, 'examples');
  const examples = fs
    .readdirSync(examplesDir)
    .filter(name => name.endsWith('.md'))
    .map(name => `examples/${name}`);
  return [...fixed, ...examples];
}

function markdownFiles() {
  const files = ['SKILL.md'];
  for (const directory of ['references', 'examples']) {
    const absoluteDirectory = path.join(root, directory);
    const entries = fs
      .readdirSync(absoluteDirectory, { withFileTypes: true })
      .filter(entry => entry.isFile() && entry.name.endsWith('.md'))
      .map(entry => entry.name)
      .sort();
    for (const entry of entries) files.push(`${directory}/${entry}`);
  }
  return files;
}

function countNotationBlocks(relativePath) {
  const lines = read(relativePath).split(/\r?\n/);
  let inFence = false;
  let count = 0;
  for (const raw of lines) {
    const trimmed = raw.trim();
    if (trimmed.startsWith('```')) {
      inFence = !inFence;
      continue;
    }
    if (inFence && notationRe.test(trimmed)) count++;
  }
  return count;
}

function runCommandValidator(relativePath) {
  const absolutePath = path.join(root, relativePath);
  const result = spawnSync(process.execPath, [commandValidator, absolutePath, '--channel', 'netease', '--quiet'], {
    encoding: 'utf8'
  });

  if (result.status !== 0) {
    fail(relativePath, 0, '未通过 validate-commands.mjs');
    if (!quiet) {
      if (result.stdout?.trim()) process.stderr.write(result.stdout);
      if (result.stderr?.trim()) process.stderr.write(result.stderr);
    }
  }
}

function runChainValidator() {
  const files = safeRuntimeFiles().map(file => path.join(root, file));
  const result = spawnSync(process.execPath, [chainValidator, ...files, '--quiet'], {
    encoding: 'utf8'
  });
  if (result.status !== 0) {
    fail('scripts/validate-chains.mjs', 0, '运行时文档未通过链级检查');
    if (!quiet) {
      if (result.stdout?.trim()) process.stderr.write(result.stdout);
      if (result.stderr?.trim()) process.stderr.write(result.stderr);
    }
  }
}

function validateRegistry() {
  const registryPath = 'references/recipe-registry.json';
  let registry;
  try {
    registry = JSON.parse(read(registryPath));
  } catch (error) {
    fail(registryPath, 0, `JSON 解析失败: ${error.message}`);
    return;
  }

  if (registry.schemaVersion !== 2) fail(registryPath, 0, 'schemaVersion 必须为 2');
  if (
    registry.target?.edition !== 'bedrock' ||
    registry.target?.channel !== 'netease-china' ||
    registry.target?.version !== '1.21.130'
  ) {
    fail(registryPath, 0, 'target 必须为网易 netease-china / bedrock 1.21.130');
  }
  if (registry.target?.commandsOnly !== true) fail(registryPath, 0, 'commandsOnly 必须为 true');

  const componentMap = new Map();
  if (!Array.isArray(registry.components)) {
    fail(registryPath, 0, 'components 必须是数组');
    return;
  }
  for (const component of registry.components) {
    if (component.id) componentMap.set(component.id, component);
  }

  for (const collection of ['components', 'recipes']) {
    if (!Array.isArray(registry[collection])) {
      fail(registryPath, 0, `${collection} 必须是数组`);
      continue;
    }
    const seen = new Set();
    for (const entry of registry[collection]) {
      if (!entry.id) {
        fail(registryPath, 0, `${collection} 中存在缺少 id 的条目`);
        continue;
      }
      if (seen.has(entry.id)) fail(registryPath, 0, `${collection} 重复 id: ${entry.id}`);
      seen.add(entry.id);

      const document = entry.file || entry.document;
      if (!document || !fs.existsSync(path.join(root, document))) {
        fail(registryPath, 0, `${entry.id} 引用了不存在的文件: ${document || '(空)'}`);
      }
      if (entry.spec && !fs.existsSync(path.join(root, entry.spec))) {
        fail(registryPath, 0, `${entry.id} 引用了不存在的 spec: ${entry.spec}`);
      }
      if (!['static-only', 'tested'].includes(entry.status)) {
        fail(registryPath, 0, `${entry.id} 的 status 必须是 static-only 或 tested`);
      }
      if (!['any', 'single-operator', 'shared-button', 'nearest-player'].includes(entry.multiplayer)) {
        fail(registryPath, 0, `${entry.id} 的 multiplayer 值未知`);
      }
      for (const field of ['objectives', 'tags', 'tests']) {
        if (entry[field] !== undefined && !Array.isArray(entry[field])) {
          fail(registryPath, 0, `${entry.id}.${field} 必须是数组`);
        }
      }
      for (const field of ['usesActionbar', 'tickingArea']) {
        if (entry[field] !== undefined && typeof entry[field] !== 'boolean') {
          fail(registryPath, 0, `${entry.id}.${field} 必须是布尔值`);
        }
      }
      if (entry.tests?.some(test => typeof test !== 'string')) {
        fail(registryPath, 0, `${entry.id}.tests 只能包含字符串`);
      }
      for (const objective of entry.objectives || []) {
        if (!/^[A-Za-z0-9_.-]+$/.test(objective)) {
          fail(registryPath, 0, `${entry.id} 的目标名不是 ASCII: ${objective}`);
        }
      }
      for (const tag of entry.tags || []) {
        if (!/^[A-Za-z0-9_.:-]+$/.test(tag)) {
          fail(registryPath, 0, `${entry.id} 的标签名不是 ASCII: ${tag}`);
        }
      }
      if (!Number.isInteger(entry.blockCount) || entry.blockCount < 1) {
        fail(registryPath, 0, `${entry.id} 缺少有效的正整数 blockCount`);
      } else if (collection === 'recipes' && document && fs.existsSync(path.join(root, document))) {
        const actual = countNotationBlocks(document);
        if (actual !== entry.blockCount) {
          fail(registryPath, 0, `${entry.id} 声明 ${entry.blockCount} 格，文档实际 ${actual} 格`);
        }
      }

      if (collection === 'recipes' && entry.moduleIds !== undefined) {
        if (!Array.isArray(entry.moduleIds)) {
          fail(registryPath, 0, `${entry.id}.moduleIds 必须是数组`);
        } else {
          let moduleTotal = 0;
          for (const moduleId of entry.moduleIds) {
            const component = componentMap.get(moduleId);
            if (!component) {
              fail(registryPath, 0, `${entry.id} 引用了不存在的模块: ${moduleId}`);
            } else {
              moduleTotal += component.blockCount;
            }
          }
          if (Number.isInteger(entry.blockCount) && moduleTotal !== entry.blockCount) {
            fail(
              registryPath,
              0,
              `${entry.id} 的 blockCount=${entry.blockCount}，但 moduleIds 合计 ${moduleTotal}`
            );
          }
        }
      }
    }
  }
}

function validateChainSpecs() {
  const examplesDirectory = path.join(root, 'examples');
  const specs = fs
    .readdirSync(examplesDirectory)
    .filter(name => name.endsWith('.spec.json'))
    .map(name => path.join(examplesDirectory, name));

  for (const spec of specs) {
    const result = spawnSync(process.execPath, [chainSpecValidator, spec, '--quiet'], {
      encoding: 'utf8'
    });
    if (result.status !== 0) {
      fail(path.relative(root, spec), 0, '未通过 validate-chain-spec.mjs');
      if (!quiet) {
        if (result.stdout?.trim()) process.stderr.write(result.stdout);
        if (result.stderr?.trim()) process.stderr.write(result.stderr);
      }
    }
  }
}

function validateChainSpecSchema() {
  const relativePath = 'assets/chain-spec.schema.json';
  let schema;
  try {
    schema = JSON.parse(read(relativePath));
  } catch (error) {
    fail(relativePath, 0, `JSON 解析失败: ${error.message}`);
    return;
  }
  if (schema.type !== 'object') fail(relativePath, 0, 'schema.type 必须是 object');
  if (!schema.properties?.blocks || !schema.$defs?.block) {
    fail(relativePath, 0, 'schema 缺少 blocks 或 block 定义');
  }
  if (!schema.properties?.channel?.enum?.includes('netease-china')) {
    fail(relativePath, 0, 'schema 必须声明 netease-china 渠道');
  }
}

function validateMarkdownLinks(relativePath) {
  const text = read(relativePath);
  const linkRe = /\[[^\]]+\]\(([^)]+)\)/g;
  for (const match of text.matchAll(linkRe)) {
    const target = match[1].trim().replace(/^<|>$/g, '').split('#')[0];
    if (!target || /^(?:https?:|mailto:)/i.test(target)) continue;
    const resolved = path.resolve(path.dirname(path.join(root, relativePath)), target);
    if (!fs.existsSync(resolved)) {
      fail(relativePath, 0, `Markdown 链接目标不存在: ${target}`);
    }
  }
}

function validateReferenceRouting() {
  const skill = read('SKILL.md');
  const referenceFiles = fs
    .readdirSync(path.join(root, 'references'), { withFileTypes: true })
    .filter(entry => entry.isFile() && entry.name.endsWith('.md'))
    .map(entry => entry.name);

  for (const file of referenceFiles) {
    const target = `references/${file}`;
    if (!skill.includes(target)) {
      fail('SKILL.md', 0, `参考文件未从入口路由: ${target}`);
    }
  }
}

function validateWikiSourceGuide() {
  const relativePath = 'references/wiki-and-sources.md';
  const text = read(relativePath);
  const required = [
    'https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/%E6%9B%B4%E6%96%B0%E4%BF%A1%E6%81%AF/3.10.html',
    'https://github.com/yixin-amore/MinecraftBE-Command-Building-Skill',
    '9184e4d36c4df62a8fc4e2be951bd9163dd8196a',
    'https://github.com/xiaobo121388/mc-bedrock-commands-skill',
    '6836bfe7ae0fd34b2eb02bd210b201294f614e57',
    'https://github.com/xiaobo121388/netease_mc-ui-skill',
    '5238ee29460792c55db73aaeba3a6a02f1869ba7',
    'https://github.com/TriM-Organization/BDXConverter',
    'b3316b6003a297c8d13f693ac40270276eff7565',
    'https://learn.microsoft.com/en-us/minecraft/creator/reference/content/rawmessagejson?view=minecraft-bedrock-stable',
    'https://learn.microsoft.com/en-us/minecraft/creator/documents/moreinfosources?view=minecraft-bedrock-stable',
    'https://learn.microsoft.com/en-us/minecraft/creator/documents/packagingaworldtemplate',
    'https://learn.microsoft.com/en-us/minecraft/creator/documents/differencesbetweenbedrockandjava?view=minecraft-bedrock-experimental',
    'https://wiki.bedrock.dev/llms.txt',
    'https://minecraft.wiki/w/Commands',
    'CC BY-NC-SA 3.0'
  ];

  for (const value of required) {
    if (!text.includes(value)) fail(relativePath, 0, `缺少关键来源或许可说明: ${value}`);
  }
  if (!/最近核对日期：\d{4}-\d{2}-\d{2}/.test(text)) {
    fail(relativePath, 0, '缺少最近核对日期');
  }
  for (const match of text.matchAll(/https?:\/\/[^\s)<>]+/g)) {
    if (!match[0].startsWith('https://')) {
      fail(relativePath, 0, `外部来源必须使用 HTTPS: ${match[0]}`);
    }
  }
}

function validateExampleStructure(relativePath) {
  if (!relativePath.startsWith('examples/') || relativePath.endsWith('README.md')) return;

  const text = read(relativePath);
  const lines = text.split(/\r?\n/);
  const ids = new Map();
  let inFence = false;
  let notationCount = 0;

  lines.forEach((raw, index) => {
    const line = index + 1;
    const trimmed = raw.trim();
    if (trimmed.startsWith('```')) {
      inFence = !inFence;
      return;
    }
    if (!inFence) return;

    const match = trimmed.match(notationRe);
    if (!match) return;

    notationCount++;
    const id = match[1];
    const settings = match[2].split(SEP).map(part => part.trim()).filter(Boolean);
    if (settings.length !== 4) {
      fail(relativePath, line, `${id} 的方块标注不是四段`);
    }
    if (ids.has(id)) {
      fail(relativePath, line, `示例内重复编号 ${id}（首次出现在 L${ids.get(id)}）`);
    } else {
      ids.set(id, line);
    }

    let next = index + 1;
    while (next < lines.length && !lines[next].trim()) next++;
    if (next >= lines.length || !lines[next].trim().startsWith('/')) {
      fail(relativePath, line, `${id} 下一行不是以 / 开头的命令`);
    }
  });

  const declared = text.match(/命令方块总数[：:]\s*(\d+)\s*个/);
  if (declared && Number(declared[1]) !== notationCount) {
    fail(relativePath, 1, `声明 ${declared[1]} 个命令方块，实际标注 ${notationCount} 个`);
  }
}

function validateWorldTemplate() {
  const relativePath = 'assets/world-template.level.dat';
  const absolutePath = path.join(root, relativePath);
  if (!fs.existsSync(absolutePath)) {
    fail(relativePath, 0, '缺少世界元数据模板');
    return;
  }
  const data = fs.readFileSync(absolutePath);
  const digest = crypto.createHash('sha256').update(data).digest('hex');
  const expected = 'fed9ce5d3dc1c5fc236288263ffa9b5bd55d8a1b53c46675e5db690324f42c92';
  if (digest !== expected) fail(relativePath, 0, `模板 SHA-256 不匹配: ${digest}`);
  if (data.length !== 2828) fail(relativePath, 0, `模板大小应为 2828 bytes，实际 ${data.length}`);
  const documentation = read('assets/WORLD_TEMPLATE.md');
  if (!documentation.includes(expected)) {
    fail('assets/WORLD_TEMPLATE.md', 0, '模板文档缺少实际 SHA-256');
  }
}

validateFrontmatter();
for (const file of safeRuntimeFiles()) runCommandValidator(file);
runChainValidator();
validateRegistry();
validateChainSpecs();
validateChainSpecSchema();
validateReferenceRouting();
validateWikiSourceGuide();
validateWorldTemplate();
for (const file of markdownFiles()) {
  validateMarkdownLinks(file);
  validateExampleStructure(file);
}

if (!quiet) {
  console.log(`Skill: ${root}`);
  console.log(`运行时文档已校验: ${safeRuntimeFiles().length}`);
  console.log(`Markdown 内部链接已校验: ${markdownFiles().length}`);
  console.log('结构化链 spec 已校验: examples/*.spec.json');
  console.log('投影世界模板已校验: assets/world-template.level.dat');
  console.log('说明: legacy-to-modern.md 故意包含错误旧语法，不按可直接运行文件整体校验。');
}

if (errors.length) {
  for (const item of errors) {
    const location = item.line ? `L${item.line}: ` : '';
    console.error(`✖ ${item.file} ${location}${item.message}`);
  }
  process.exit(1);
}

if (!quiet) console.log('通过: skill 结构、运行时命令和示例方块总数一致。');
