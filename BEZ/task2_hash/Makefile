CC = g++
CFLAGS =-std=c++11 -Wall -Werror -pedantic -O2
LDFLAGS =-lcrypto

all: hash

hash: hash.cpp
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean: hash
	rm $<

.PHONY: clean
