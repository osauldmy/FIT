CC = gcc
CFLAGS =-std=c99 -Wall -Werror -pedantic -O2
LDFLAGS =-lcrypto

all: encrypt

encrypt: encrypt.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean: encrypt
	rm $<

.PHONY: clean
