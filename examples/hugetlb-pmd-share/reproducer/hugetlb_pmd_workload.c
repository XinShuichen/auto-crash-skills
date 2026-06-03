// SPDX-License-Identifier: MIT
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define DEFAULT_HUGEPAGES 512UL
#define DEFAULT_CHILDREN 2UL
#define DEFAULT_LOOPS 100UL
#define HUGEPAGE_SIZE (2UL * 1024UL * 1024UL)
#define TASK_NAME "hpmd_workload"

static void die(const char *msg)
{
	perror(msg);
	exit(EXIT_FAILURE);
}

static unsigned long parse_ulong(const char *text, const char *name)
{
	char *end = NULL;
	unsigned long value;

	errno = 0;
	value = strtoul(text, &end, 0);
	if (errno || !end || *end != '\0' || value == 0) {
		fprintf(stderr, "invalid %s: %s\n", name, text);
		exit(EXIT_FAILURE);
	}

	return value;
}

static void set_task_name(void)
{
	if (prctl(PR_SET_NAME, TASK_NAME, 0, 0, 0) != 0)
		die("prctl(PR_SET_NAME)");
}

static void touch_range(void *addr, size_t len)
{
	volatile char *p = addr;
	size_t off;

	for (off = 0; off < len; off += HUGEPAGE_SIZE)
		p[off] = (char)(off / HUGEPAGE_SIZE);
}

static void read_exact_ready(int fd, unsigned long children)
{
	unsigned long ready = 0;

	while (ready < children) {
		char byte;
		ssize_t ret = read(fd, &byte, 1);

		if (ret == 1) {
			ready++;
			continue;
		}
		if (ret < 0 && errno == EINTR)
			continue;
		if (ret == 0) {
			fprintf(stderr, "ready pipe closed after %lu/%lu children\n",
				ready, children);
			exit(EXIT_FAILURE);
		}
		die("read ready pipe");
	}
}

static void child_body(int fd, int ready_fd, size_t len)
{
	void *map;
	char ready = 'r';

	set_task_name();

	map = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (map == MAP_FAILED)
		die("child mmap");

	touch_range(map, len);
	if (write(ready_fd, &ready, 1) != 1)
		die("write ready pipe");

	usleep(250000);

	if (munmap(map, len) != 0)
		die("child munmap");

	_exit(EXIT_SUCCESS);
}

static void run_one_loop(const char *base_path, unsigned long loop,
			 unsigned long children, size_t len)
{
	char path[PATH_MAX];
	int fd;
	int ready_pipe[2];
	void *map;
	unsigned long i;

	if (snprintf(path, sizeof(path), "%s.%ld.%lu",
		     base_path, (long)getpid(), loop) >= (int)sizeof(path)) {
		fprintf(stderr, "path too long\n");
		exit(EXIT_FAILURE);
	}

	fd = open(path, O_CREAT | O_EXCL | O_RDWR, 0600);
	if (fd < 0)
		die("open hugetlbfs file");

	if (ftruncate(fd, (off_t)len) != 0)
		die("ftruncate hugetlbfs file");

	map = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (map == MAP_FAILED)
		die("parent mmap");

	touch_range(map, len);

	if (pipe(ready_pipe) != 0)
		die("pipe");

	for (i = 0; i < children; i++) {
		pid_t pid = fork();

		if (pid < 0)
			die("fork");
		if (pid == 0) {
			close(ready_pipe[0]);
			child_body(fd, ready_pipe[1], len);
		}
	}

	close(ready_pipe[1]);
	read_exact_ready(ready_pipe[0], children);
	close(ready_pipe[0]);

	if (munmap(map, len) != 0)
		die("parent munmap");

	for (i = 0; i < children; i++) {
		int status;

		if (wait(&status) < 0)
			die("wait");
		if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
			fprintf(stderr, "child failed, status=0x%x\n", status);
			exit(EXIT_FAILURE);
		}
	}

	close(fd);
	if (unlink(path) != 0)
		die("unlink hugetlbfs file");
}

int main(int argc, char **argv)
{
	const char *base_path;
	unsigned long hugepages = DEFAULT_HUGEPAGES;
	unsigned long children = DEFAULT_CHILDREN;
	unsigned long loops = DEFAULT_LOOPS;
	size_t len;
	unsigned long loop;

	if (argc < 2 || argc > 5) {
		fprintf(stderr,
			"usage: %s <hugetlbfs-file-prefix> [2m-hugepages] [children] [loops]\n",
			argv[0]);
		return EXIT_FAILURE;
	}

	base_path = argv[1];
	if (argc > 2)
		hugepages = parse_ulong(argv[2], "2m-hugepages");
	if (argc > 3)
		children = parse_ulong(argv[3], "children");
	if (argc > 4)
		loops = parse_ulong(argv[4], "loops");

	set_task_name();

	if (hugepages > SIZE_MAX / HUGEPAGE_SIZE) {
		fprintf(stderr, "mapping length overflow\n");
		return EXIT_FAILURE;
	}
	len = (size_t)hugepages * HUGEPAGE_SIZE;

	printf("hugetlb PMD workload: prefix=%s hugepages=%lu bytes=%zu children=%lu loops=%lu\n",
	       base_path, hugepages, len, children, loops);
	fflush(stdout);

	for (loop = 0; loop < loops; loop++) {
		run_one_loop(base_path, loop, children, len);
		if ((loop + 1) % 10 == 0 || loop + 1 == loops) {
			printf("completed loop %lu/%lu\n", loop + 1, loops);
			fflush(stdout);
		}
	}

	return EXIT_SUCCESS;
}
