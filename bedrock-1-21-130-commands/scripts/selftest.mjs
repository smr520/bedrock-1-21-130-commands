#!/usr/bin/env node
/**
 * 无第三方依赖的脚本回归测试。
 * 用法: node selftest.mjs
 */

import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bedrock-skill-'));

function writeFixture(name, text) {
  const file = path.join(tempDir, name);
  fs.writeFileSync(file, text, 'utf8');
  return file;
}

function run(script, args) {
  return spawnSync(process.execPath, [path.join(scriptDir, script), ...args], {
    encoding: 'utf8'
  });
}

function expectStatus(result, expected, label) {
  assert.equal(
    result.status,
    expected,
    `${label}\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`
  );
}

try {
  const validChain = writeFixture(
    'valid-chain.md',
    [
      '# valid',
      '```text',
      'V1【循环｜无条件｜保持开启｜延迟0】',
      '/scoreboard players add @a test 0',
      '',
      'V2【连锁｜无条件｜保持开启｜延迟0】',
      '/scoreboard players remove @a[scores={test=1..}] test 1',
      '```'
    ].join('\n')
  );
  expectStatus(run('validate-chains.mjs', [validChain, '--strict', '--quiet']), 0, '有效链应通过');

  const invalidChain = writeFixture(
    'invalid-chain.md',
    [
      '# invalid',
      '```text',
      'X1【循环｜无条件｜保持开启｜延迟0】',
      '/scoreboard players add @a test 0',
      '',
      'X2【脉冲｜无条件｜需要红石｜延迟0】',
      '/scoreboard players remove @a[scores={test=1..}] test 1',
      '```'
    ].join('\n')
  );
  expectStatus(run('validate-chains.mjs', [invalidChain, '--quiet']), 1, '非连锁后继应失败');

  const warningChain = writeFixture(
    'warning-chain.md',
    [
      '# warning',
      '```text',
      'W1【脉冲｜无条件｜需要红石｜延迟0】',
      '/execute as @p run give @s apple 1',
      '',
      'W2【连锁｜有条件｜保持开启｜延迟0】',
      '/execute as @p run clear @s apple 0 1',
      '```'
    ].join('\n')
  );
  expectStatus(run('validate-chains.mjs', [warningChain, '--strict', '--quiet']), 1, '严格模式应拒绝警告');

  const validCommand = writeFixture(
    'valid-command.txt',
    '/execute as @a[scores={coins=1..}] run scoreboard players remove @s coins 1\n'
  );
  expectStatus(run('validate-commands.mjs', [validCommand, '--quiet']), 0, '现代命令应通过');

  const invalidCommand = writeFixture(
    'invalid-command.txt',
    '/execute @a ~ ~ ~ scoreboard players add @s coins 1\n'
  );
  expectStatus(run('validate-commands.mjs', [invalidCommand, '--quiet']), 1, '旧 execute 应失败');

  const explicitReplaceitem = writeFixture(
    'explicit-replaceitem.txt',
    '/replaceitem entity @a slot.hotbar 8 destroy snowball 16 0 {"minecraft:item_lock":{"mode":"lock_in_slot"}}\n'
  );
  expectStatus(run('validate-commands.mjs', [explicitReplaceitem, '--quiet']), 0, '显式 replaceitem 应通过');

  const legacyReplaceitem = writeFixture(
    'legacy-replaceitem.txt',
    '/replaceitem entity @a slot.hotbar 8 snowball 16 0 {"minecraft:item_lock":{"mode":"lock_in_slot"}}\n'
  );
  const legacyReplaceResult = run('validate-commands.mjs', [legacyReplaceitem]);
  expectStatus(legacyReplaceResult, 0, '旧 replaceitem 重载仍可作为兼容输入');
  assert.match(legacyReplaceResult.stdout, /destroy 或 keep/);

  const planner = run('plan-recipes.mjs', ['server-starter-core', 'player-hud', '--json']);
  expectStatus(planner, 0, '配方计划器应通过');
  const plan = JSON.parse(planner.stdout);
  assert.equal(plan.nominalBlocks, 14);
  assert.equal(plan.totalBlocks, 13);
  assert.equal(plan.reusedBlocks, 1);
  assert.deepEqual(plan.sharedModules['display-bus'], ['server-starter-core', 'player-hud']);

  const unknownRecipe = run('plan-recipes.mjs', ['not-a-recipe', '--json']);
  expectStatus(unknownRecipe, 1, '未知配方应失败');

  console.log('通过: 校验器正向、负向、严格模式、命令语法和配方复用测试。');
} catch (error) {
  console.error(`✖ selftest: ${error.message}`);
  process.exitCode = 1;
} finally {
  fs.rmSync(tempDir, { recursive: true, force: true });
}
