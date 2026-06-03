# 修复 Commit 搜索

修复搜索回答两个问题：哪个 commit 能切断 producer frontier，以及现场内核是否已经包含它。

## 前置条件

搜索前先在 ECTM 写清 producer frontier。不要用 panic 函数名、fault 地址、日志文本、OOM 文本或 retry 症状作为主搜索锚点。

## 搜索范围

- 现场内核源码只用于本地机制分析。
- 有 upstream Linux cache 时，用它搜索修复。
- 优先 `stable/linux-<major>.<minor>.y`，其次主线分支。
- 分析过程中不要依赖实时网络 fetch。

## 搜索锚点

优先：

- producer 函数或 helper 返回点；
- 同一共享对象和字段；
- writer-side 更新、重绑定、重配置；
- 引用计数、锁、RCU、内存序、快照修改；
- 进入 consumer 前的校验。

降权：

- consumer 兜底或防御检查；
- 仅日志修改；
- 已包含提交；
- 对象形态或调用路径不匹配；
- 只修相似症状但属于不同顶层操作的提交，除非它修改了实际栈使用的同一个共享 helper。

## 反向排序

升格候选前，要写清为什么看起来更像的症状匹配不是主修复。如果候选只修改后续 delete/remove 检查，而 producer frontier 是更早的 helper 返回、被跳过的 writer 更新，或引用计数语义误用，那么该候选应降权。

对 refcount/mapcount/rmap 类问题，按“最早让计数出错的边”排序：

1. 修正 helper 语义、防止错误跳过；
2. 修正 caller 控制流、恢复 writer 更新；
3. 计数更新处的 writer-side 锁或顺序修复；
4. consumer-side 复查、重试或移除断言。

## 候选排序

| Rank | Commit | Title | Change site | Mechanism match | Included? | Conclusion |
|---|---|---|---|---|---|---|
| 1 | `<sha>` | ... | producer frontier | high | no | main fix |

主修复必须说明它切断机制链中的哪一条边。
