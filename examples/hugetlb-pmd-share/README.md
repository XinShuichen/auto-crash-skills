# hugetlb PMD Sharing Validation Example

[Chinese document](README.zh-CN.md)

This example documents the expected local validation shape for a hugetlbfs
eviction/truncate panic. The public repository does not include a crash dump,
`vmlinux`, or kernel source files.

## Local Inputs

Put local-only files outside git tracking:

```text
local-testdata/hugetlb-pmd-share/
  dump
  vmlinux
  linux-source/      # or an absolute symlink to the matching source tree
```

Then ask Codex to use `kernel-crash-debugger` with those paths and the matching
kernel source.

## Reference Panic

```text
kernel BUG at fs/hugetlbfs/inode.c:515!
RIP: remove_inode_hugepages
```

## Deterministic Reproducer

The natural race can be rare. [reproducer](reproducer/) contains a debug-only
kernel module plus a hugetlbfs workload:

- `hugetlb_pmd_ref_injector.c`: kretprobe module that adds one transient
  reference to the PMD page-table page when `huge_pmd_unshare()` sees
  `page_count == 1`.
- `hugetlb_pmd_workload.c`: file-backed hugetlbfs workload that drives PMD
  sharing, unmap, and inode eviction across forked processes.

Build on the target kernel:

```bash
make -C examples/hugetlb-pmd-share/reproducer
```

Run on an affected kernel with kdump enabled and enough 2 MiB HugeTLB pages for
a PUD-sized mapping:

```bash
sudo mount -t hugetlbfs none /mnt/huge
sudo insmod examples/hugetlb-pmd-share/reproducer/hugetlb_pmd_ref_injector.ko \
  max_injections=1 comm_filter=hpmd_workload
examples/hugetlb-pmd-share/reproducer/hugetlb_pmd_workload \
  /mnt/huge/hpmd-test 512 2 100
```

This module is not a production workaround. It only forces the old
`page_count()` sharing test into the wrong branch for validation. Confirm
success from kdump dmesg: `kernel BUG at fs/hugetlbfs/inode.c:515!`.

See [expected-result.md](expected-result.md) for the expected analysis shape.

## Blind Validation Transcript

The raw Codex session transcript is available as
[session-019e8e85-transcript.html](session-019e8e85-transcript.html).
