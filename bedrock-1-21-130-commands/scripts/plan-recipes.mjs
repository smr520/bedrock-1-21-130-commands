#!/usr/bin/env node
/**
 * 组合已登记配方，计算方块预算、复用模块和状态冲突。
 * 用法: node plan-recipes.mjs <recipe-id...> [--json]
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const asJson = process.argv.includes('--json');
const requested = process.argv.slice(2).filter(arg => !arg.startsWith('--'));
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(scriptDir);
const registryPath = path.join(root, 'references', 'recipe-registry.json');
const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
const recipes = new Map(registry.recipes.map(recipe => [recipe.id, recipe]));
const components = new Map(registry.components.map(component => [component.id, component]));

if (registry.schemaVersion !== 2) {
  console.error(`不支持 registry schemaVersion ${registry.schemaVersion}；需要 2`);
  process.exit(1);
}

if (!requested.length) {
  console.log('可用配方:');
  for (const recipe of registry.recipes) {
    const flags = [
      recipe.usesActionbar ? '动作栏' : '',
      recipe.tickingArea ? '常加载' : '',
      recipe.moduleIds?.length ? `复用模块 ${recipe.moduleIds.length}` : ''
    ].filter(Boolean);
    const suffix = flags.length ? `（${flags.join('，')}）` : '';
    console.log(`- ${recipe.id}: ${recipe.blockCount} CB${suffix}`);
  }
  process.exit(0);
}

const selected = [];
const missing = [];
for (const id of new Set(requested)) {
  const recipe = recipes.get(id);
  if (recipe) selected.push(recipe);
  else missing.push(id);
}

if (missing.length) {
  console.error(`未知配方: ${missing.join(', ')}`);
  process.exit(1);
}

const objectiveUsage = new Map();
const tagUsage = new Map();
const moduleUsage = new Map();
const standaloneModules = new Map();
const actionbarKeys = new Set();
const tests = new Set();
const multiplayerModes = new Set();
const notLiveTested = [];
let nominalBlocks = 0;
let needsTickingArea = false;

function addUsage(map, key, owner) {
  if (!map.has(key)) map.set(key, []);
  const owners = map.get(key);
  if (!owners.includes(owner)) owners.push(owner);
}

for (const recipe of selected) {
  nominalBlocks += recipe.blockCount;
  needsTickingArea ||= Boolean(recipe.tickingArea);
  multiplayerModes.add(recipe.multiplayer);
  if (recipe.status !== 'tested') notLiveTested.push(recipe.id);

  if (recipe.moduleIds?.length) {
    for (const moduleId of recipe.moduleIds) {
      const component = components.get(moduleId);
      if (!component) {
        console.error(`${recipe.id} 引用了不存在的模块: ${moduleId}`);
        process.exit(1);
      }
      addUsage(moduleUsage, moduleId, recipe.id);
      if (component.usesActionbar) actionbarKeys.add(`module:${moduleId}`);
    }
  } else {
    standaloneModules.set(`recipe:${recipe.id}`, recipe.blockCount);
    if (recipe.usesActionbar) actionbarKeys.add(`recipe:${recipe.id}`);
  }

  for (const objective of recipe.objectives || []) addUsage(objectiveUsage, objective, recipe.id);
  for (const tag of recipe.tags || []) addUsage(tagUsage, tag, recipe.id);
  for (const test of recipe.tests || []) tests.add(test);
}

const moduleBlocks = [...moduleUsage.keys()].reduce(
  (sum, moduleId) => sum + components.get(moduleId).blockCount,
  0
);
const standaloneBlocks = [...standaloneModules.values()].reduce((sum, count) => sum + count, 0);
const totalBlocks = moduleBlocks + standaloneBlocks;
const reusedBlocks = nominalBlocks - totalBlocks;
const sharedObjectives = [...objectiveUsage.entries()].filter(([, owners]) => owners.length > 1);
const sharedTags = [...tagUsage.entries()].filter(([, owners]) => owners.length > 1);
const sharedModules = [...moduleUsage.entries()].filter(([, owners]) => owners.length > 1);
const risks = [];

if (actionbarKeys.size > 1) risks.push('multiple-actionbar-consumers');
if (multiplayerModes.has('single-operator') && multiplayerModes.size > 1) {
  risks.push('mixed-single-operator-zones');
}
if (multiplayerModes.has('nearest-player')) risks.push('nearest-player-attribution');
if (sharedTags.length) risks.push('shared-temporary-tags');
if (moduleUsage.has('display-arbiter') && actionbarKeys.size > 1) {
  risks.push('remove-standalone-actionbar-outputs');
}

const result = {
  recipes: selected.map(recipe => recipe.id),
  nominalBlocks,
  totalBlocks,
  reusedBlocks,
  modules: [...moduleUsage.keys()].sort(),
  sharedModules: Object.fromEntries(sharedModules),
  objectives: [...objectiveUsage.keys()].sort(),
  sharedObjectives: Object.fromEntries(sharedObjectives),
  tags: [...tagUsage.keys()].sort(),
  sharedTags: Object.fromEntries(sharedTags),
  usesActionbar: actionbarKeys.size > 0,
  actionbarConsumers: actionbarKeys.size,
  needsTickingArea,
  multiplayerModes: [...multiplayerModes].sort(),
  risks,
  notLiveTested,
  tests: [...tests].sort()
};

if (asJson) {
  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

console.log(`配方: ${result.recipes.join(', ')}`);
console.log(`名义方块总数: ${result.nominalBlocks}`);
console.log(`复用后总数: ${result.totalBlocks}`);
console.log(`复用减少: ${result.reusedBlocks}`);
console.log(`共享模块: ${result.modules.join(', ') || '无'}`);
console.log(`记分板目标: ${result.objectives.join(', ') || '无'}`);
console.log(`标签: ${result.tags.join(', ') || '无'}`);
console.log(`动作栏输出: ${result.actionbarConsumers}`);
console.log(`常加载区: ${result.needsTickingArea ? '需要' : '不需要'}`);
console.log(`多人模式: ${result.multiplayerModes.join(', ')}`);

if (sharedModules.length) {
  console.log('\n组合后只计一次的共享模块:');
  for (const [moduleId, owners] of sharedModules) {
    console.log(`- ${moduleId}: ${owners.join(', ')}`);
  }
}
if (sharedObjectives.length) {
  console.log('\n共享目标（必须确认含义和初始化兼容）:');
  for (const [objective, owners] of sharedObjectives) {
    console.log(`- ${objective}: ${owners.join(', ')}`);
  }
}
if (sharedTags.length) {
  console.log('\n共享临时标签（不同动作应改名，避免中途互抢）:');
  for (const [tag, owners] of sharedTags) {
    console.log(`- ${tag}: ${owners.join(', ')}`);
  }
}
if (actionbarKeys.size > 1) {
  console.log('\n风险: 存在多个独立动作栏输出，必须合并显示或按状态只启用一个。');
}
if (moduleUsage.has('display-arbiter') && actionbarKeys.size > 1) {
  console.log('提示: 已选择 HUD 仲裁模板；接入时删除对应玩法自己的 titleraw actionbar，不需要把仲裁格和原显示格相加。');
}
if (multiplayerModes.has('single-operator') && multiplayerModes.size > 1) {
  console.log('风险: 同时选择单人操作区和多人模式，需要分别规划操作区域。');
}
if (multiplayerModes.has('nearest-player')) {
  console.log('风险: nearest-player 配方在多人拥挤时可能把操作归给附近另一名玩家。');
}
if (notLiveTested.length) {
  console.log(`\n实机状态: ${notLiveTested.join(', ')} 仅为静态检查。`);
}
if (result.tests.length) {
  console.log(`\n建议测试: ${result.tests.join('; ')}`);
}
