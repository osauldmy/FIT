#include <bitset>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>

#include <cstring>

#include <openssl/evp.h>

const char *const HASH = "sha384";

std::string generate_random_string() {
  const std::string alphabet =
      "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

  std::mt19937_64 mt{static_cast<std::uint_fast64_t>(
      std::chrono::high_resolution_clock::now().time_since_epoch().count())};

  std::uniform_int_distribution<unsigned> string_length{5, 100};
  std::uniform_int_distribution<unsigned> alphabet_indices{
      0, static_cast<unsigned>(alphabet.length() - 1)};

  std::string random_string = "";

  for (unsigned i{0}; i < string_length(mt); i++) {
    random_string += alphabet.at(alphabet_indices(mt));
  }

  return random_string;
}

bool generate_hash(const std::string &random_string, std::string &string_hash) {
  EVP_MD_CTX *ctx;
  const EVP_MD *type;
  unsigned char hash[EVP_MAX_MD_SIZE];
  unsigned hash_length;

  OpenSSL_add_all_digests();

  if (!(type = EVP_get_digestbyname(HASH))) {
    std::cerr << "error: hash " << HASH << " doesn't exist!\n";
    return false;
  }

  if ((ctx = EVP_MD_CTX_new()) == NULL) {
    std::cerr << "error: creating new context failed\n";
    return false;
  }

  if (!EVP_DigestInit_ex(ctx, type, NULL)) {
    std::cerr << "error: EVP_DigestInit_ex failed\n";
    EVP_MD_CTX_free(ctx);
    return false;
  }

  if (!EVP_DigestUpdate(ctx, random_string.c_str(), random_string.length())) {
    std::cerr << "error: EVP_DigestUpdate failed\n";
    EVP_MD_CTX_free(ctx);
    return false;
  }

  if (!EVP_DigestFinal_ex(ctx, hash, &hash_length)) {
    std::cerr << "error: EVP_DigestFinal_ex failed\n";
    EVP_MD_CTX_free(ctx);
    return false;
  }

  EVP_MD_CTX_free(ctx);

  string_hash = std::string(reinterpret_cast<char *>(hash), hash_length);
  return true;
}

bool check_hash_is_valid(const std::string &hash, size_t amount_of_zeros) {
  size_t found_zeros = 0;

  for (char symbol : hash) {

    auto bits = std::bitset<8>(symbol);

    for (size_t i{8}; i > 0; i--) {

      if (bits[i - 1] == 0) {
        found_zeros++;
      } else if (bits[i - 1] != 0 && found_zeros < amount_of_zeros) {
        return false;
      }
    }

    if (found_zeros >= amount_of_zeros) {
      break;
    }
  }

  return true;
}

int main(int argc, char *argv[]) {

  if (argc != 2 || !std::strncmp(argv[1], "-", 1)) {
    std::cerr << "usage: ./hash positive_number_of_leading_zero_bits\n";
    return 1;
  }

  size_t leading_zero_bits_amount = std::strtoul(argv[1], NULL, 10);

  if (leading_zero_bits_amount == 0 || leading_zero_bits_amount == ULONG_MAX) {
    std::cerr << "error: invalid or out of range amount\n";
    return 1;
  }

  std::string random_string;
  std::string hash;

  while (true) {

    random_string = generate_random_string();

    if (!generate_hash(random_string, hash)) {
      return 1;
    }

    if (check_hash_is_valid(hash, leading_zero_bits_amount)) {
      break;
    }
  }

  for (int symbol : random_string) {
    std::cout << std::setfill('0') << std::setw(2) << std::hex << symbol;
  }
  std::cout << std::endl;

  for (unsigned char symbol : hash) {
    std::cout << std::setfill('0') << std::setw(2) << std::hex
              << static_cast<int16_t>(symbol);
  }
  std::cout << std::endl;
  return 0;
}
