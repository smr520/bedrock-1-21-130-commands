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

  const namedEntitySelector = writeFixture(
    'named-entity-selector.txt',
    '/execute as @e[name="Bob"] run say selected\n'
  );
  expectStatus(
    run('validate-commands.mjs', [namedEntitySelector, '--quiet']),
    0,
    '按 name 精确筛选实体应通过'
  );

  const predicateSelector = writeFixture(
    'predicate-selector.txt',
    '/execute as @e[predicate=test] run say invalid\n'
  );
  const predicateSelectorResult = run('validate-commands.mjs', [predicateSelector]);
  expectStatus(predicateSelectorResult, 1, 'Java predicate 选择器参数应失败');
  assert.match(predicateSelectorResult.stdout, /Java 参数 predicate=/);

  const advancementsSelector = writeFixture(
    'advancements-selector.txt',
    '/execute as @a[advancements={story/root=true}] run say invalid\n'
  );
  expectStatus(
    run('validate-commands.mjs', [advancementsSelector, '--quiet']),
    1,
    'Java advancements 选择器参数应失败'
  );

  const conditionOnlyBlock = writeFixture(
    'condition-only-block.txt',
    '/execute if block ~ ~-1 ~ stone\n'
  );
  expectStatus(run('validate-commands.mjs', [conditionOnlyBlock, '--quiet']), 0, '完整条件型 execute 应通过');

  const conditionOnlyScore = writeFixture(
    'condition-only-score.txt',
    '/execute as @a if score @s coins matches 1..\n'
  );
  expectStatus(run('validate-commands.mjs', [conditionOnlyScore, '--quiet']), 0, '带上下文的条件型 execute 应通过');

  const modifierOnlyExecute = writeFixture(
    'modifier-only-execute.txt',
    '/execute as @a\n'
  );
  expectStatus(run('validate-commands.mjs', [modifierOnlyExecute, '--quiet']), 1, '只有修饰子命令的 execute 应失败');

  const incompleteCondition = writeFixture(
    'incomplete-condition.txt',
    '/execute if entity\n'
  );
  expectStatus(run('validate-commands.mjs', [incompleteCondition, '--quiet']), 1, '不完整条件型 execute 应失败');

  const replacementCharacter = writeFixture(
    'replacement-character.txt',
    '/say 损坏字符\uFFFD\n'
  );
  const replacementCharacterResult = run('validate-commands.mjs', [replacementCharacter]);
  expectStatus(replacementCharacterResult, 1, '包含 U+FFFD 的文件应失败');
  assert.match(replacementCharacterResult.stdout, /U\+FFFD/);

  const singleTargetScore = writeFixture(
    'single-target-score.txt',
    '/execute if score @a[tag=pair,c=1] coins = @s coins run say equal\n'
  );
  expectStatus(
    run('validate-commands.mjs', [singleTargetScore, '--quiet']),
    0,
    'if score 两侧为单一目标时应通过'
  );

  const pluralTargetScore = writeFixture(
    'plural-target-score.txt',
    '/execute if score @a[tag=pair] coins = @s coins run say equal\n'
  );
  const pluralTargetScoreResult = run('validate-commands.mjs', [pluralTargetScore]);
  expectStatus(pluralTargetScoreResult, 1, 'if score 使用多目标选择器时应失败');
  assert.match(pluralTargetScoreResult.stdout, /必须解析为单一目标/);

  const singleMatchesScore = writeFixture(
    'single-matches-score.txt',
    '/execute as @a if score @s coins matches 1.. run say positive\n'
  );
  expectStatus(run('validate-commands.mjs', [singleMatchesScore, '--quiet']), 0, 'if score matches 单目标应通过');

  const pluralMatchesScore = writeFixture(
    'plural-matches-score.txt',
    '/execute if score @a[tag=pair] coins matches 1.. run say positive\n'
  );
  const pluralMatchesScoreResult = run('validate-commands.mjs', [pluralMatchesScore]);
  expectStatus(pluralMatchesScoreResult, 1, 'if score matches 使用多目标选择器时应失败');
  assert.match(pluralMatchesScoreResult.stdout, /目标必须解析为单一实体/);

  const countedPluralScore = writeFixture(
    'counted-plural-score.txt',
    '/execute if score @p[c=2] coins = @s coins run say equal\n'
  );
  const countedPluralScoreResult = run('validate-commands.mjs', [countedPluralScore]);
  expectStatus(countedPluralScoreResult, 1, '@p 使用 c>1 时也应视为多目标');
  assert.match(countedPluralScoreResult.stdout, /可能匹配多个实体/);

  const singleTeleportDestination = writeFixture(
    'single-teleport-destination.txt',
    '/execute as @a[c=1] run tp @s @a[tag=destination,c=1]\n'
  );
  expectStatus(
    run('validate-commands.mjs', [singleTeleportDestination, '--quiet']),
    0,
    'tp 目的地位于单目标选择器时应通过'
  );

  const pluralTeleportDestination = writeFixture(
    'plural-teleport-destination.txt',
    '/execute as @s run tp @s @a[tag=destination]\n'
  );
  const pluralTeleportDestinationResult = run('validate-commands.mjs', [pluralTeleportDestination]);
  expectStatus(pluralTeleportDestinationResult, 1, 'tp 目的地使用多目标选择器时应失败');
  assert.match(pluralTeleportDestinationResult.stdout, /目的地必须解析为单一实体/);

  const countedPluralTeleportDestination = writeFixture(
    'counted-plural-teleport-destination.txt',
    '/execute as @s run tp @s @r[c=3]\n'
  );
  expectStatus(
    run('validate-commands.mjs', [countedPluralTeleportDestination, '--quiet']),
    1,
    'tp 目的地使用 @r c>1 时应失败'
  );

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

  const neteaseUnverified = writeFixture(
    'netease-unverified.txt',
    '/camera @a set default\n'
  );
  const neteaseUnverifiedResult = run('validate-commands.mjs', [neteaseUnverified]);
  expectStatus(neteaseUnverifiedResult, 0, '网易未验证命令应警告但允许人工确认后使用');
  assert.match(neteaseUnverifiedResult.stdout, /网易 1\.21\.130 默认未验证/);

  const neteaseFog = writeFixture(
    'netease-fog.txt',
    '/fog @a push minecraft:fog_default\n'
  );
  const neteaseFogResult = run('validate-commands.mjs', [neteaseFog]);
  expectStatus(neteaseFogResult, 0, '网易证据冲突的 fog 应警告但不硬判不存在');
  assert.match(neteaseFogResult.stdout, /官方资料存在冲突/);

  const neteaseTitleraw = writeFixture(
    'netease-titleraw.txt',
    '/titleraw @a actionbar {"rawtext":[{"text":"测试"}]}\n'
  );
  const neteaseTitlerawResult = run('validate-commands.mjs', [neteaseTitleraw]);
  expectStatus(neteaseTitlerawResult, 0, '网易 titleraw 应警告但允许人工确认后使用');
  assert.match(neteaseTitlerawResult.stdout, /网易 1\.21\.130 默认未验证/);

  expectStatus(
    run('validate-commands.mjs', [neteaseUnverified, '--channel', 'international', '--quiet']),
    0,
    '国际版模式不应套用网易未验证警告'
  );

  const tellrawWithCommandWords = writeFixture(
    'tellraw-command-words.txt',
    '/tellraw @a {"rawtext":[{"text":"run camera"}]}\n'
  );
  const tellrawWordsResult = run('validate-commands.mjs', [tellrawWithCommandWords]);
  expectStatus(tellrawWordsResult, 0, '文本里的 run camera 不应误判成嵌套命令');
  assert.doesNotMatch(tellrawWordsResult.stdout, /网易 1\.21\.130 默认未验证/);

  const conditionalRawtext = writeFixture(
    'conditional-rawtext.txt',
    `/tellraw @a ${JSON.stringify({
      rawtext: [
        { text: '任务：' },
        {
          translate: '%%2',
          with: {
            rawtext: [
              { selector: '@s[scores={quest=1}]' },
              { text: '已领取' }
            ]
          }
        }
      ]
    })}\n`
  );
  expectStatus(
    run('validate-commands.mjs', [conditionalRawtext, '--quiet']),
    0,
    '参数数量完整的 translate %%2 条件文本应通过'
  );

  const invalidConditionalRawtext = writeFixture(
    'invalid-conditional-rawtext.txt',
    `/tellraw @a ${JSON.stringify({
      rawtext: [{ translate: '%%2', with: { rawtext: [{ text: '只有一个参数' }] } }]
    })}\n`
  );
  const invalidConditionalRawtextResult = run('validate-commands.mjs', [invalidConditionalRawtext]);
  expectStatus(invalidConditionalRawtextResult, 1, 'translate %%2 参数不足时应失败');
  assert.match(invalidConditionalRawtextResult.stdout, /translate %%2 需要至少 2 个 with 参数/);

  const validSpec = writeFixture(
    'valid-spec.json',
    JSON.stringify({
      name: 'valid-spec',
      channel: 'netease-china',
      targetVersion: '1.21.130',
      commandsOnly: true,
      setup: ['scoreboard objectives add timer dummy'],
      blocks: [
        {
          id: 'B1',
          type: 'repeat',
          condition: 'unconditional',
          redstone: 'always_active',
          delay: 0,
          command: 'scoreboard players add .tick timer 1',
          next: null
        }
      ],
      tests: ['activate the chain and verify the score increments']
    })
  );
  const validSpecPlan = path.join(tempDir, 'valid-spec-plan.md');
  expectStatus(
    run('validate-chain-spec.mjs', [validSpec, '--write', validSpecPlan, '--quiet']),
    0,
    '有效 spec 应通过'
  );
  assert.ok(fs.existsSync(validSpecPlan));

  const invalidSpec = writeFixture(
    'invalid-spec.json',
    JSON.stringify({
      name: 'invalid-spec',
      channel: 'netease-china',
      targetVersion: '1.21.130',
      commandsOnly: true,
      blocks: [
        {
          id: 'B1',
          type: 'chain',
          command: 'say no head',
          next: null
        }
      ]
    })
  );
  expectStatus(
    run('validate-chain-spec.mjs', [invalidSpec, '--quiet']),
    1,
    '没有链头的 chain spec 应失败'
  );

  const invalidProjectionSpec = writeFixture(
    'invalid-projection-spec.json',
    JSON.stringify({
      name: 'invalid-projection',
      channel: 'netease-china',
      targetVersion: '1.21.130',
      commandsOnly: true,
      projection: { axis: 'diagonal' },
      blocks: [
        {
          id: 'B1',
          type: 'impulse',
          command: 'say invalid projection',
          next: null
        }
      ]
    })
  );
  const invalidProjectionResult = run('validate-chain-spec.mjs', [invalidProjectionSpec]);
  expectStatus(invalidProjectionResult, 1, '非法 projection.axis 应失败');
  assert.match(invalidProjectionResult.stdout, /PROJECTION_AXIS/);

  const mixedPositionsSpec = writeFixture(
    'mixed-positions-spec.json',
    JSON.stringify({
      name: 'mixed-positions',
      channel: 'netease-china',
      targetVersion: '1.21.130',
      commandsOnly: true,
      blocks: [
        {
          id: 'B1',
          type: 'impulse',
          command: 'say first',
          next: 'B2',
          pos: [0, 4, 0],
          facing: 'east'
        },
        {
          id: 'B2',
          type: 'chain',
          command: 'say second',
          next: null
        }
      ]
    })
  );
  const mixedPositionsResult = run('validate-chain-spec.mjs', [mixedPositionsSpec]);
  expectStatus(mixedPositionsResult, 1, '部分 block 写 pos 时应失败');
  assert.match(mixedPositionsResult.stdout, /MIXED_POSITIONS/);

  const planner = run('plan-recipes.mjs', ['server-starter-core', 'player-hud', '--json']);
  expectStatus(planner, 0, '配方计划器应通过');
  const plan = JSON.parse(planner.stdout);
  assert.equal(plan.nominalBlocks, 14);
  assert.equal(plan.totalBlocks, 13);
  assert.equal(plan.reusedBlocks, 1);
  assert.deepEqual(plan.sharedModules['display-bus'], ['server-starter-core', 'player-hud']);

  const unknownRecipe = run('plan-recipes.mjs', ['not-a-recipe', '--json']);
  expectStatus(unknownRecipe, 1, '未知配方应失败');

  const python = process.platform === 'win32' ? 'python' : 'python3';
  const projectionExport = spawnSync(
    python,
    ['-B', '-X', 'utf8', path.join(scriptDir, 'export-projection.py'), '--self-test'],
    { encoding: 'utf8' }
  );
  expectStatus(projectionExport, 0, 'MCWorld/BDS 投影导出器自测应通过');

  console.log(
    '通过: 校验器正向、负向、严格模式、命令语法、Java 选择器参数、rawtext 参数槽、spec、投影导出、单目标分数比较、传送目的地和配方复用测试。'
  );
} catch (error) {
  console.error(`✖ selftest: ${error.message}`);
  process.exitCode = 1;
} finally {
  fs.rmSync(tempDir, { recursive: true, force: true });
}
