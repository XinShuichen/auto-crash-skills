# Expected Analysis Shape

[Chinese document](expected-result.zh-CN.md)

A successful analysis should not stop at `remove_inode_hugepages()`. It should
prove this chain:

1. The panic is `kernel BUG at fs/hugetlbfs/inode.c:515!`.
2. The crash is in `remove_inode_hugepages()` in truncate/evict context.
3. `page_mapped(page)` returns true because the hugetlb compound mapcount still
   indicates a mapping.
4. Normal hugetlb unmap should remove rmap for the real page.
5. Old `huge_pmd_unshare()` can mistake temporary PMD page-table references for
   sharing and skip the real page's rmap removal.
6. The main fix is `94b4b41d0cdf5cfd4d4325bc0e6e9e0d0e996133`; the original
   upstream commit is `59d9094df3d79443937add8700b2ef1a866b1081`.

Other local or distro backport SHAs are acceptable only when they carry the
same upstream original and mechanism.
