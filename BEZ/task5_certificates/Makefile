CC = gcc
CFLAGS =-std=c99 -Wall -Werror -pedantic -O2
LDFLAGS =-lssl -lcrypto

all: connect

connect: connect.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean: connect
	rm $<

.PHONY: clean
