KDIR ?= /lib/modules/$(shell uname -r)/build

obj-m += hugetlb_pmd_ref_injector.o

all: module workload

module:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules

workload: hugetlb_pmd_workload

hugetlb_pmd_workload: hugetlb_pmd_workload.c
	$(CC) -O2 -Wall -Wextra -o $@ $<

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean
	rm -rf .tmp_versions
	rm -f hugetlb_pmd_workload *.ko *.mod *.mod.c *.o *.order *.symvers .*.cmd
