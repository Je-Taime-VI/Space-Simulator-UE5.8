# WorldScape Plugin Production Integration Tutorial (English)

Asset ID: UE-PLG-0050

## Goal

Build a maintainable production integration for WorldScape Plugin. The target capability set is 行星地形, 无缝大世界, 程序噪声, 植被流送, 世界体积, 重力与示例角色. Start with an isolated demo map, then expose the solution through a project-owned `WorldScapePluginAdapter`.

## Structure

Use Config and Data folders for auditable presets, Runtime for the adapter and state machine, UI for snapshot-only presentation, Tests for minimum, stress and multiplayer maps, and a project source module for stable interfaces.

## Implementation Sequence

1. Install the exact package and prove the default example in a clean project.
2. Create WorldScapePluginAdapter with Initialize, Start, Cancel, GetSnapshot and Shutdown operations.
3. Implement 行星地形 as the first minimum flow, including invalid input and cancellation.
4. Add 无缝大世界, 程序噪声 and 植被流送 one at a time with dedicated regression cases.
5. Add explicit limits for jobs, queues, instances, memory and per-frame work.
6. Package Development and Shipping builds, verify on a clean environment, then perform upgrade and rollback rehearsals.

## State Model

Use Disabled, Initializing, Ready, Running, Cancelling, Succeeded, Failed and ShuttingDown. Only the adapter changes state. Every asynchronous request receives an ID and obsolete callbacks are ignored. Travel, destruction, logout and shutdown cancel work and release delegates, timers, resources and handles.

## Data Contract

Store stable IDs, schema version, business state and required parameters. Never use display text, array positions or transient object pointers as persistent identity. Validate external paths, network data, player input, counts and schemas before vendor logic. Preserve an Unknown branch for future enum or error values.

## Performance

Bound concurrency, queue length, cache size, instance count and frame budget. Replace global Tick scans with events, partitions, timers or incremental work. Profile game-thread time, GPU cost, memory peaks, garbage collection, queue backlog and cleanup after unload.

## Multiplayer

Server authority validates identity, ownership, distance, state and quantities. Client prediction is visual only. Verify dedicated and listen servers, two independent clients, late join, reconnect and ownership transfer where relevant.

## Test Plan

- Configuration validation and state transitions
- 行星地形, 无缝大世界, 程序噪声, 植被流送, 世界体积, 重力与示例角色
- Invalid input, cancellation, timeout and dependency failure
- Maximum load and long-running soak test
- Map travel, destruction and application shutdown
- Development and Shipping in a clean environment
- Upgrade, old data migration and rollback

## Release Checklist

The original root structure is intact; package, engine mapping and SHA-256 are recorded; Chinese and English official/custom tutorials are present; diagnostics contain no secrets; minimum and stress results are documented; and the exact rollback package is available.
