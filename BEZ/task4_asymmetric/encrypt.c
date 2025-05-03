#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/rand.h>

#define BUFFER_SIZE 4096
#define DEFAULT_CIPHER "aes-256-cbc"
#define CIPHER_NAME_LEN 11

void print_header(const char *const cipher, unsigned char *iv,
                  unsigned char *ek, int ek_length) {
  printf("cipher: %s, cipher length: %lu\n", cipher, strlen(cipher));

  printf("iv length: %lu\n\t", strlen((char *)iv));

  for (size_t i = 0; i < strlen((char *)iv); i++) {
    printf("%02x", iv[i]);
  }

  printf("\nstrlen(ek): %lu\nek_length: %d\n\t", strlen((char *)ek), ek_length);
  for (size_t i = 0; i < strlen((char *)ek); i++) {
    printf("%02x", ek[i]);
  }
  printf("\n");
}

bool read_header(FILE *data_file_ptr, char *cipher, unsigned char *iv,
                 unsigned char **ek, int *ek_length) {

  if (!fread(cipher, CIPHER_NAME_LEN, 1, data_file_ptr) ||
      feof(data_file_ptr) || ferror(data_file_ptr)) {
    return false;
  }
  cipher[CIPHER_NAME_LEN] = '\0';

  if (!fread(iv, EVP_MAX_IV_LENGTH, 1, data_file_ptr) || feof(data_file_ptr) ||
      ferror(data_file_ptr)) {
    return false;
  }
  iv[EVP_MAX_IV_LENGTH] = '\0';

  if (!fread(ek_length, sizeof(*ek_length), 1, data_file_ptr) ||
      feof(data_file_ptr) || ferror(data_file_ptr)) {
    return false;
  }

  *ek = (unsigned char *)malloc((*ek_length) + 1);
  if (*ek == NULL) {
    // sometimes fails because of negative value read
    fprintf(stderr, "error: malloc failed\n");
    fprintf(stderr, "ek_length + 1: %d\n", (*ek_length) + 1);
    return false;
  }

  if (!fread(*ek, *ek_length, 1, data_file_ptr) || feof(data_file_ptr) ||
      ferror(data_file_ptr)) {
    return false;
  }

  return true;
}

bool write_header(FILE *output_file_ptr, const char *const cipher,
                  unsigned char *iv, unsigned char *ek, int ek_length) {

  if (!fwrite(cipher, strlen(cipher), 1, output_file_ptr) ||
      ferror(output_file_ptr)) {
    return false;
  }

  if (!fwrite(iv, strlen((char *)iv), 1, output_file_ptr) ||
      ferror(output_file_ptr)) {
    return false;
  }

  if (!fwrite(&ek_length, sizeof(ek_length), 1, output_file_ptr) ||
      ferror(output_file_ptr)) {
    return false;
  }

  if (!fwrite(ek, ek_length, 1, output_file_ptr) || ferror(output_file_ptr)) {
    return false;
  }

  return true;
}

bool decrypt(FILE *key_file_ptr, FILE *data_file_ptr, FILE *output_file_ptr) {

  EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();

  if (!ctx) {
    fprintf(stderr, "error: EVP_CIPHER_CTX_new() failed\n");
    return false;
  }

  int ek_length = 0;
  char cipher_name[CIPHER_NAME_LEN + 1];
  unsigned char iv[EVP_MAX_IV_LENGTH + 1];
  unsigned char *ek = NULL;

  if (!read_header(data_file_ptr, cipher_name, iv, &ek, &ek_length)) {
    fprintf(stderr, "error: cannot read header\n");
    free(ek);
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  ek[ek_length] = '\0';

  /* print_header(cipher_name, iv, ek, ek_length); */

  const EVP_CIPHER *cipher = EVP_get_cipherbyname(cipher_name);
  if (!cipher) {
    fprintf(stderr, "error: invalid cipher\n");
    free(ek);
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  EVP_PKEY *privkey = PEM_read_PrivateKey(key_file_ptr, NULL, NULL, NULL);

  if (!privkey) {
    fprintf(stderr, "error: PEM_read_PrivateKey() failed\n");
    free(ek);
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  if (!EVP_OpenInit(ctx, cipher, ek, ek_length, iv, privkey)) {
    fprintf(stderr, "error: EVPOpenInit() failed\n");
    free(ek);
    EVP_PKEY_free(privkey);
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  free(ek);
  EVP_PKEY_free(privkey);

  unsigned char input_buffer[BUFFER_SIZE],
      output_buffer[BUFFER_SIZE + EVP_MAX_BLOCK_LENGTH];
  int input_buffer_length = 0, output_buffer_length = 0;

  while (true) {
    input_buffer_length =
        fread(input_buffer, sizeof(*input_buffer), BUFFER_SIZE, data_file_ptr);

    if (input_buffer_length <= 0 && feof(data_file_ptr)) {
      break;
    }

    if (ferror(data_file_ptr)) {
      fprintf(stderr, "error: ferror on read from data file\n");
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }

    if (!EVP_OpenUpdate(ctx, output_buffer, &output_buffer_length, input_buffer,
                        input_buffer_length)) {
      fprintf(stderr, "error: EVP_OpenUpdate() failed\n");
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }

    if (!fwrite(output_buffer, sizeof(*output_buffer), output_buffer_length,
                output_file_ptr) ||
        ferror(output_file_ptr)) {

      fprintf(stderr, "error: ferror on write to output file\n");
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }
  }

  if (!EVP_OpenFinal(ctx, output_buffer, &output_buffer_length)) {
    fprintf(stderr, "error: EVP_OpenFinal() failed\n");
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  if (output_buffer_length > 0) {
    if (!fwrite(output_buffer, sizeof(*output_buffer), output_buffer_length,
                output_file_ptr) ||
        ferror(output_file_ptr)) {

      fprintf(stderr, "error: ferror on write to output file\n");
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }
  }

  EVP_CIPHER_CTX_free(ctx);
  return true;
}

bool encrypt(FILE *key_file_ptr, FILE *data_file_ptr, FILE *output_file_ptr,
             const char *const cipher_name) {

  EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
  if (!ctx) {
    fprintf(stderr, "error: EVP_CIPHER_CTX_new() failed\n");
    return false;
  }

  const EVP_CIPHER *cipher = EVP_get_cipherbyname(cipher_name);
  if (!cipher) {
    fprintf(stderr, "error: invalid cipher\n");
    return false;
  }

  EVP_PKEY *pubkey = PEM_read_PUBKEY(key_file_ptr, NULL, NULL, NULL);
  if (!pubkey) {
    fprintf(stderr, "error: PEM_read_PUBKEY() failed\n");
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  int ek_length = 0;
  unsigned char iv[EVP_MAX_IV_LENGTH + 1];
  unsigned char *ek = (unsigned char *)malloc(EVP_PKEY_size(pubkey) + 1);
  iv[EVP_MAX_IV_LENGTH] = '\0';
  ek[EVP_PKEY_size(pubkey)] = '\0';

  if (!ek) {
    fprintf(stderr, "error: malloc failed\n");
    EVP_PKEY_free(pubkey);
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  int npubk = 1;
  if (npubk != EVP_SealInit(ctx, cipher, &ek, &ek_length, iv, &pubkey, npubk)) {
    fprintf(stderr, "error: EVP_SealInit failed\n");
    free(ek);
    EVP_PKEY_free(pubkey);
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  /* print_header(cipher_name, iv, ek, ek_length); */

  if (!write_header(output_file_ptr, cipher_name, iv, ek, ek_length)) {
    fprintf(stderr, "error: cannot write header\n");
    free(ek);
    EVP_PKEY_free(pubkey);
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  free(ek);
  EVP_PKEY_free(pubkey);

  unsigned char input_buffer[BUFFER_SIZE],
      output_buffer[BUFFER_SIZE + EVP_MAX_BLOCK_LENGTH];
  int input_buffer_length = 0, output_buffer_length = 0;

  while (true) {

    input_buffer_length =
        fread(input_buffer, sizeof(*input_buffer), BUFFER_SIZE, data_file_ptr);

    if (input_buffer_length <= 0 && feof(data_file_ptr)) {
      break;
    }

    if (ferror(data_file_ptr)) {
      fprintf(stderr, "error: ferror on read from data file\n");
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }

    if (!EVP_SealUpdate(ctx, output_buffer, &output_buffer_length, input_buffer,
                        input_buffer_length)) {

      fprintf(stderr, "error: EVP_SealUpdate failed\n");
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }

    if (!fwrite(output_buffer, sizeof(*output_buffer), output_buffer_length,
                output_file_ptr) ||
        ferror(output_file_ptr)) {

      fprintf(stderr, "error: ferror on write to output file\n");
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }
  }

  if (!EVP_SealFinal(ctx, output_buffer, &output_buffer_length)) {
    fprintf(stderr, "error: EVP_SealFinal failed\n");
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  if (output_buffer_length > 0) {
    if (!fwrite(output_buffer, sizeof(*output_buffer), output_buffer_length,
                output_file_ptr) ||
        ferror(output_file_ptr)) {

      fprintf(stderr, "error: ferror on write to output file\n");
      EVP_CIPHER_CTX_free(ctx);
      return 0;
    }
  }

  EVP_CIPHER_CTX_free(ctx);
  return 1;
}

bool run(int argc, char **argv) {

  if (argc < 5 || argc > 6 ||
      (strncmp(argv[1], "e", 2) && strncmp(argv[1], "d", 2))) {
    fprintf(
        stderr,
        "usage: ./encrypt ACTION PUBLICKEY FILEIN FILEOUT [CIPHERNAME]\n\n"
        "ACTION      = {e,d}      {en,de}crypting mode\n"
        "PKEY        = arg        path to {public, private} key\n"
        "FILEIN      = arg        path to input file\n"
        "FILEOUT     = arg        name of output file\n"
        "CIPHERNAME  = arg        optional name of the cipher with key size "
        "and cipher mode for EVP_get_cipherbyname()\n"
        "                         Default: aes-256-cbc\n");
    return false;
  }

  bool to_encrypt = argv[1][0] == 'e';
  const char *const key_filename = argv[2];
  const char *const data_filename = argv[3];
  const char *const output_filename = argv[4];
  const char *const cipher_name = argc == 6 ? argv[5] : DEFAULT_CIPHER;

  FILE *key_file_ptr = fopen(key_filename, "r");
  FILE *data_file_ptr = fopen(data_filename, "rb");
  FILE *output_file_ptr = fopen(output_filename, "wb");

  if (!key_file_ptr) {
    fprintf(
        stderr,
        "error: key file \"%s\" should exist and be a regular file with read "
        "permissions\n",
        key_filename);
    fclose(data_file_ptr);
    fclose(output_file_ptr);
    return false;
  }

  if (!data_file_ptr) {
    fprintf(stderr,
            "error: data file \"%s\" should exist and be a regular file with "
            "read "
            "permissions\n",
            data_filename);
    fclose(key_file_ptr);
    fclose(output_file_ptr);
    return false;
  }

  if (!output_file_ptr) {
    fprintf(stderr, "error: cannot open output file (\"%s\") for writing\n",
            output_filename);
    fclose(key_file_ptr);
    fclose(data_file_ptr);
    return false;
  }

  OpenSSL_add_all_ciphers();

  bool success;
  if (to_encrypt) {
    success =
        encrypt(key_file_ptr, data_file_ptr, output_file_ptr, cipher_name);
  } else {
    success = decrypt(key_file_ptr, data_file_ptr, output_file_ptr);
  }

  fclose(key_file_ptr);
  fclose(data_file_ptr);
  fclose(output_file_ptr);

  if (!success) {
    if (remove(output_filename) != 0) {
      fprintf(stderr, "error: cannot remove %s\n", output_filename);
    }
    return false;
  }

  return true;
}

int main(int argc, char **argv) {

  if (RAND_load_file("/dev/random", 32) != 32) {
    fprintf(stderr, "error: sorry, cannot seed the random generator!\n");
    return 2;
  }

  if (!run(argc, argv)) {
    return 1;
  }

  return 0;
}
