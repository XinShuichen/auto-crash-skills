// SPDX-License-Identifier: GPL-2.0
/*
 * Debug-only reproducer for the old hugetlb PMD sharing page_count() test.
 *
 * On affected kernels, huge_pmd_unshare() used page_count(virt_to_page(ptep))
 * to decide whether a PMD page-table page was shared. This module injects one
 * transient page reference when that count is 1, so the old test takes the
 * unshare branch even though the PMD page-table page is not shared.
 */
#include <linux/atomic.h>
#include <linux/kprobes.h>
#include <linux/mm.h>
#include <linux/module.h>
#include <linux/ptrace.h>
#include <linux/sched.h>
#include <linux/string.h>

#if defined(CONFIG_X86_64)
#define HPREF_ARG4(regs) ((void *)((regs)->cx))
#elif defined(CONFIG_ARM64)
#define HPREF_ARG4(regs) ((void *)((regs)->regs[3]))
#else
#error "hugetlb_pmd_ref_injector supports x86_64 and arm64 argument registers"
#endif

struct injection_data {
	struct page *pt_page;
	pte_t *ptep;
	int count_before;
	bool injected;
};

static char symbol_name[KSYM_NAME_LEN] = "huge_pmd_unshare";
static char comm_filter[TASK_COMM_LEN] = "hpmd_workload";
static int max_injections = 1;
static int trigger_count = 1;
static int maxactive = 64;
static bool verbose = true;

static atomic_t injection_count = ATOMIC_INIT(0);

module_param_string(symbol_name, symbol_name, sizeof(symbol_name), 0444);
MODULE_PARM_DESC(symbol_name, "Function to probe, default huge_pmd_unshare");
module_param_string(comm_filter, comm_filter, sizeof(comm_filter), 0644);
MODULE_PARM_DESC(comm_filter, "Task comm filter; empty string matches all tasks");
module_param(max_injections, int, 0644);
MODULE_PARM_DESC(max_injections, "Maximum injections; negative means unlimited");
module_param(trigger_count, int, 0644);
MODULE_PARM_DESC(trigger_count, "Inject only when page_count(pte_page) matches this value");
module_param(maxactive, int, 0444);
MODULE_PARM_DESC(maxactive, "kretprobe maxactive value");
module_param(verbose, bool, 0644);
MODULE_PARM_DESC(verbose, "Emit pr_info for injected calls");

static bool reserve_injection_slot(void)
{
	int old;

	if (max_injections < 0) {
		atomic_inc(&injection_count);
		return true;
	}

	do {
		old = atomic_read(&injection_count);
		if (old >= max_injections)
			return false;
	} while (atomic_cmpxchg(&injection_count, old, old + 1) != old);

	return true;
}

static bool task_matches(void)
{
	if (!comm_filter[0])
		return true;

	return strcmp(current->comm, comm_filter) == 0;
}

static int hpref_entry_handler(struct kretprobe_instance *ri,
			       struct pt_regs *regs)
{
	struct injection_data *data = (struct injection_data *)ri->data;
	struct page *pt_page;
	pte_t *ptep;
	int count;

	data->injected = false;

	if (!task_matches())
		return 0;

	ptep = HPREF_ARG4(regs);
	if (!ptep || !virt_addr_valid(ptep))
		return 0;

	pt_page = virt_to_page(ptep);
	count = page_count(pt_page);
	if (count != trigger_count)
		return 0;

	if (!reserve_injection_slot())
		return 0;

	get_page(pt_page);
	data->pt_page = pt_page;
	data->ptep = ptep;
	data->count_before = count;
	data->injected = true;

	if (verbose)
		pr_info("hugetlb_pmd_ref_injector: injected transient ref ptep=%px count_before=%d comm=%s total=%d\n",
			ptep, count, current->comm, atomic_read(&injection_count));

	return 0;
}

static int hpref_ret_handler(struct kretprobe_instance *ri,
			     struct pt_regs *regs)
{
	struct injection_data *data = (struct injection_data *)ri->data;
	unsigned long ret;

	if (!data->injected)
		return 0;

	ret = regs_return_value(regs);
	put_page(data->pt_page);

	if (verbose)
		pr_info("hugetlb_pmd_ref_injector: released transient ref ptep=%px ret=%lu count_before=%d count_after=%d\n",
			data->ptep, ret, data->count_before,
			page_count(data->pt_page));

	return 0;
}

static struct kretprobe hpref_probe = {
	.entry_handler = hpref_entry_handler,
	.handler = hpref_ret_handler,
	.data_size = sizeof(struct injection_data),
};

static int __init hpref_init(void)
{
	int ret;

	hpref_probe.kp.symbol_name = symbol_name;
	hpref_probe.maxactive = maxactive;

	ret = register_kretprobe(&hpref_probe);
	if (ret < 0) {
		pr_err("hugetlb_pmd_ref_injector: register_kretprobe(%s) failed: %d\n",
		       symbol_name, ret);
		return ret;
	}

	pr_info("hugetlb_pmd_ref_injector: probing %s comm_filter=%s max_injections=%d trigger_count=%d\n",
		symbol_name, comm_filter[0] ? comm_filter : "<all>",
		max_injections, trigger_count);
	return 0;
}

static void __exit hpref_exit(void)
{
	unregister_kretprobe(&hpref_probe);
	pr_info("hugetlb_pmd_ref_injector: unregistered, injections=%d missed=%d\n",
		atomic_read(&injection_count), hpref_probe.nmissed);
}

module_init(hpref_init);
module_exit(hpref_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Auto Crash Skills");
MODULE_DESCRIPTION("Debug reproducer for old hugetlb PMD page_count sharing test");
