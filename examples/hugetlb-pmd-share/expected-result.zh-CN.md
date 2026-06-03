# 预期分析形态

[English document](expected-result.md)

成功分析不应停在 `remove_inode_hugepages()`。它应证明如下链路：

1. panic 为 `kernel BUG at fs/hugetlbfs/inode.c:515!`。
2. 崩溃位于 `remove_inode_hugepages()` 的 truncate/evict 语义。
3. `page_mapped(page)` 返回 true，因为 hugetlb compound mapcount 仍显示 mapped。
4. 正常 hugetlb unmap 应对真实 page 执行 rmap 删除。
5. 旧版 `huge_pmd_unshare()` 可能把 PMD page-table 的临时引用误判为共享，并跳过
   真实 page 的 rmap 删除。
6. 主修复为 `94b4b41d0cdf5cfd4d4325bc0e6e9e0d0e996133`；上游原始提交为
   `59d9094df3d79443937add8700b2ef1a866b1081`。

其他本地或发行版 backport SHA 只有在携带同一 upstream 原始提交和同一机制时才可
接受。
