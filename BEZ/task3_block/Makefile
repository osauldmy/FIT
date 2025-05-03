CC = g++
CFLAGS =-std=c++17 -Wall -Werror -pedantic -O2
LDFLAGS =-lcrypto -lstdc++fs

all: block

block: block.cpp
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean: block
	rm $<

.PHONY: clean
