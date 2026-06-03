# hugetlb PMD 共享验证示例

[English document](README.md)

本示例记录 hugetlbfs evict/truncate panic 的本地验证形态。公开仓库不包含 crash
dump、`vmlinux` 或 kernel source 文件。

## 本地输入

把本地文件放在不进入 git 的目录中：

```text
local-testdata/hugetlb-pmd-share/
  dump
  vmlinux
  linux-source/      # 或指向匹配源码树的绝对路径 symlink
```

随后让 Codex 使用 `kernel-crash-debugger`，并提供这些路径和匹配的 kernel source。

## 参考 Panic

```text
kernel BUG at fs/hugetlbfs/inode.c:515!
RIP: remove_inode_hugepages
```

## 确定性 Reproducer

自然竞态可能较低频。[reproducer](reproducer/) 里包含 debug-only kernel module
和 hugetlbfs workload：

- `hugetlb_pmd_ref_injector.c`：kretprobe module，在 `huge_pmd_unshare()`
  看到 `page_count == 1` 时给 PMD page-table page 增加一次临时引用。
- `hugetlb_pmd_workload.c`：file-backed hugetlbfs workload，通过 fork 后的
  共享映射触发 PMD sharing、unmap 和 inode eviction。

在目标内核上编译：

```bash
make -C examples/hugetlb-pmd-share/reproducer
```

在受影响内核上运行；需要启用 kdump，并准备足够的 2 MiB HugeTLB pages 来覆盖一个
PUD-sized mapping：

```bash
sudo mount -t hugetlbfs none /mnt/huge
sudo insmod examples/hugetlb-pmd-share/reproducer/hugetlb_pmd_ref_injector.ko \
  max_injections=1 comm_filter=hpmd_workload
examples/hugetlb-pmd-share/reproducer/hugetlb_pmd_workload \
  /mnt/huge/hpmd-test 512 2 100
```

该 module 不是生产规避方案，只是为了验证旧 `page_count()` 共享判定会进入错误分支。
成功标准是 kdump dmesg 中出现 `kernel BUG at fs/hugetlbfs/inode.c:515!`。

预期分析形态见 [expected-result.zh-CN.md](expected-result.zh-CN.md)。

## Blind Validation Transcript

Codex 原始 session transcript 见
[session-019e8e85-transcript.html](session-019e8e85-transcript.html)。
