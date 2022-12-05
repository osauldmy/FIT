#ifndef __PROGTEST__
#include <assert.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#endif /* __PROGTEST__ */

typedef struct block {
  int size;
  struct block *next;
  struct block *prev;
  uint8_t *self;
  bool free;
} Block;

Block *first = NULL;
int initialMemSize = 0;
unsigned pendingBlkCount = 0;

void HeapInit(void *memPool, int memSize) {
  first = (Block *)memPool;
  pendingBlkCount = 0;
  initialMemSize = memSize;

  first->free = true;
  first->size = memSize - sizeof(*first);
  first->prev = NULL;
  first->next = NULL;
  /* kind of magic number, for verifying */
  first->self = (uint8_t *)first;
}

void *HeapAlloc(int size) {

  Block *head = first;

  while (head) {

    if (head->free == true && head->size >= size) {

      head->free = false;
      int leftFreeSize = head->size - size - sizeof(Block);
      head->size = size;
      assert(head->self != NULL);

      pendingBlkCount++;

      if (leftFreeSize > 0) {
        Block *next = (Block *)(head->self + sizeof(Block) + size);
        next->free = true;
        next->size = leftFreeSize;

        next->next = head->next;
        if (next->next != NULL) {
          next->next->prev = next;
        }

        head->next = next;
        next->prev = head;
        next->self = (uint8_t *)next;
      }
      return (void *)(((uint8_t *)head) + sizeof(*head));
    }

    head = head->next;
  }

  return NULL;
}

bool HeapFree(void *blk) {

  if (blk < (void *)(first->self) ||
      blk > (void *)(first->self + initialMemSize)) {
    return false;
  }

  Block *header = (Block *)(((uint8_t *)blk) - sizeof(Block));

  if (header->self != (uint8_t *)(header)) {
    return false;
  }

  /* Already free */
  if (header->free == true) {
    return false;
  }

  header->free = true;
  Block *next = header->next;
  Block *prev = header->prev;

  if (next != NULL && next->free == true) {

    header->size += (next->size + sizeof(Block));
    if (next->next != NULL) {
      next->next->prev = header;
    }
    header->next = next->next;
  }

  if (prev != NULL && prev->free == true) {
    header->prev->size = header->prev->size + header->size + sizeof(Block);
    header->prev->next = header->next;

    if (header->next != NULL) {
      header->next->prev = header->prev;
    }
  }
  pendingBlkCount--;
  return true;
}

void HeapDone(int *pendingBlk) { *pendingBlk = pendingBlkCount; }

#ifndef __PROGTEST__
int main(void) {
  uint8_t *p0, *p1, *p2, *p3, *p4;
  int pendingBlk;
  static uint8_t memPool[3 * 1048576];

  HeapInit(memPool, 2097152);
  assert((p0 = (uint8_t *)HeapAlloc(512000)) != NULL);
  memset(p0, 0, 512000);
  assert((p1 = (uint8_t *)HeapAlloc(511000)) != NULL);
  memset(p1, 0, 511000);
  assert((p2 = (uint8_t *)HeapAlloc(26000)) != NULL);
  memset(p2, 0, 26000);
  HeapDone(&pendingBlk);
  assert(pendingBlk == 3);

  HeapInit(memPool, 2097152);
  assert((p0 = (uint8_t *)HeapAlloc(1000000)) != NULL);
  memset(p0, 0, 1000000);
  assert((p1 = (uint8_t *)HeapAlloc(250000)) != NULL);
  memset(p1, 0, 250000);
  assert((p2 = (uint8_t *)HeapAlloc(250000)) != NULL);
  memset(p2, 0, 250000);
  assert((p3 = (uint8_t *)HeapAlloc(250000)) != NULL);
  memset(p3, 0, 250000);
  assert((p4 = (uint8_t *)HeapAlloc(50000)) != NULL);
  memset(p4, 0, 50000);
  assert(HeapFree(p2));
  assert(HeapFree(p4));
  assert(HeapFree(p3));
  assert(HeapFree(p1));
  assert((p1 = (uint8_t *)HeapAlloc(500000)) != NULL);
  memset(p1, 0, 500000);
  assert(HeapFree(p0));
  assert(HeapFree(p1));
  HeapDone(&pendingBlk);
  assert(pendingBlk == 0);

  HeapInit(memPool, 2359296);
  assert((p0 = (uint8_t *)HeapAlloc(1000000)) != NULL);
  memset(p0, 0, 1000000);
  assert((p1 = (uint8_t *)HeapAlloc(500000)) != NULL);
  memset(p1, 0, 500000);
  assert((p2 = (uint8_t *)HeapAlloc(500000)) != NULL);
  memset(p2, 0, 500000);
  assert((p3 = (uint8_t *)HeapAlloc(500000)) == NULL);
  assert(HeapFree(p2));
  assert((p2 = (uint8_t *)HeapAlloc(300000)) != NULL);
  memset(p2, 0, 300000);
  assert(HeapFree(p0));
  assert(HeapFree(p1));
  HeapDone(&pendingBlk);
  assert(pendingBlk == 1);

  HeapInit(memPool, 2359296);
  assert((p0 = (uint8_t *)HeapAlloc(1000000)) != NULL);
  memset(p0, 0, 1000000);
  assert(!HeapFree(p0 + 1000));
  HeapDone(&pendingBlk);
  assert(pendingBlk == 1);

  return 0;
}
#endif /* __PROGTEST__ */
