#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

#include <endian.h>
#include <openssl/aes.h>
#include <openssl/evp.h>

// NOTE: can be done as extra CLI param, but particular homework doesn't test it
const int KEY_LENGTH_BITS = 128; // 128, 192, 256

static const unsigned char KEY[] = "lorem ipsum dolor sit amet";
static const unsigned char IV[] = "0123456789876543210";

const unsigned BUFFER_SIZE = 4096;

bool copy_header(std::ifstream &input, std::ofstream &output) {

  char header_buffer1[4]{0};
  char header_buffer2[10]{0};

  uint8_t image_id_bytes = 0;
  uint16_t colormap_length = 0;
  uint8_t colormap_depth = 0;

  input.read(reinterpret_cast<char *>(&image_id_bytes), sizeof(image_id_bytes));
  input.read(header_buffer1, sizeof(header_buffer1));
  input.read(reinterpret_cast<char *>(&colormap_length),
             sizeof(colormap_length));
  input.read(reinterpret_cast<char *>(&colormap_depth), sizeof(colormap_depth));
  input.read(header_buffer2, sizeof(header_buffer2));

  output.write(reinterpret_cast<const char *>(&image_id_bytes),
               sizeof(image_id_bytes));
  output.write(header_buffer1, sizeof(header_buffer1));
  output.write(reinterpret_cast<const char *>(&colormap_length),
               sizeof(colormap_length));
  output.write(reinterpret_cast<const char *>(&colormap_depth),
               sizeof(colormap_depth));
  output.write(header_buffer2, sizeof(header_buffer2));

  if (htole16((uint16_t)image_id_bytes) != 0) {
    char buffer[256]{0};
    input.read(buffer, htole16((uint16_t)image_id_bytes) * sizeof(uint8_t));
    output.write(buffer, htole16((uint16_t)image_id_bytes) * sizeof(uint8_t));
  }

  if (htole16(colormap_length) != 0) {
    unsigned dynamic_header_buffer_size =
        htole16(colormap_length) * (htole16((uint16_t)colormap_depth) / 8);

    char *dynamic_header_buffer = new char[dynamic_header_buffer_size]{0};

    input.read(dynamic_header_buffer, dynamic_header_buffer_size);
    output.write(dynamic_header_buffer, dynamic_header_buffer_size);

    delete[] dynamic_header_buffer;
  }

  if (!input) {
    std::cerr << "error: unable to read header" << std::endl;
    return false;
  }

  if (!output) {
    std::cerr << "error: unable to write header" << std::endl;
    return false;
  }

  return true;
}

/*
 * Using a code snippet from `man EVP_CipherInit_ex`, which I've slightly
 * modified.
 */
bool do_crypt(std::ifstream &input, std::ofstream &output,
              const EVP_CIPHER *cipher, int crypt, const std::string &op_mode) {

  unsigned char input_buffer[BUFFER_SIZE];
  unsigned char output_buffer[BUFFER_SIZE + EVP_MAX_BLOCK_LENGTH];
  int input_buffer_length = 0, output_buffer_length = 0;

  EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
  EVP_CipherInit_ex(ctx, cipher, NULL, NULL, NULL, crypt);

  OPENSSL_assert(
      EVP_CIPHER_CTX_key_length(ctx) ==
      (op_mode == "xts" ? (KEY_LENGTH_BITS / 8) * 2 : KEY_LENGTH_BITS / 8));
  OPENSSL_assert(EVP_CIPHER_CTX_iv_length(ctx) == (op_mode == "ecb" ? 0 : 16));

  EVP_CipherInit_ex(ctx, cipher, NULL, KEY, IV, crypt);

  while (true) {

    input.read(reinterpret_cast<char *>(input_buffer), sizeof(input_buffer));

    if (!input.good() && !input.eof()) {
      std::cerr << "error: issues with reading from file\n";
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }

    input_buffer_length = input.gcount();
    if (input_buffer_length <= 0) {
      break;
    }

    if (!EVP_CipherUpdate(ctx, output_buffer, &output_buffer_length,
                          input_buffer, input_buffer_length)) {
      std::cerr << "error: EVP_CipherUpdate failed" << std::endl;
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }

    if (!output.write(reinterpret_cast<char *>(output_buffer),
                      output_buffer_length)) {
      std::cerr << "error: issues writing to file\n";
      EVP_CIPHER_CTX_free(ctx);
      return false;
    }
  }

  if (!EVP_CipherFinal_ex(ctx, output_buffer, &output_buffer_length)) {
    std::cerr << "error: EVP_CipherFinal_ex failed" << std::endl;
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  if (!output.write(reinterpret_cast<char *>(output_buffer),
                    output_buffer_length)) {
    std::cerr << "error: issues writing to file\n";
    EVP_CIPHER_CTX_free(ctx);
    return false;
  }

  EVP_CIPHER_CTX_free(ctx);
  return true;
}

void fallback(std::ofstream &output,
              const std::filesystem::path &output_filename) {

  // explicit close is not required because of RAII, but in particular
  // case it makes sense because of possible removal below.
  if (output.is_open()) {
    output.close();
  }

  if (std::filesystem::exists(output_filename)) {
    std::filesystem::remove(output_filename);
  }
}

int main(int argc, char *argv[]) {

  if (argc != 4 || !(argv[1][0] == 'e' || argv[1][0] == 'd')) {
    std::cerr
        << "usage: ./block ACTION MODE FILENAME\n\n"
        << "ACTION   = {e,d}          [e]ncryption or [d]encryption\n"
        << "MODE     = {ecb,cbc,...}  operational mode of the block cipher\n"
        << "FILENAME = arg            file to {en,de}crypt\n";
    return 1;
  }

  bool to_encrypt = argv[1][0] == 'e' ? true : false;
  std::string op_mode = argv[2];
  std::filesystem::path input_filename(argv[3]);

  OpenSSL_add_all_ciphers();
  std::string cipher_name =
      "aes-" + std::to_string(KEY_LENGTH_BITS) + "-" + op_mode;
  const EVP_CIPHER *cipher = EVP_get_cipherbyname(cipher_name.c_str());

  if (!cipher) {
    std::cerr << "error: invalid cipher mode!\n";
    return 1;
  }

  try {
    if (!std::filesystem::exists(input_filename) ||
        !std::filesystem::is_regular_file(input_filename)) {

      std::cerr
          << "error: " << input_filename
          << " does not exist, is not readable or is not a regular file\n";
      return 1;
    }
  } catch (const std::filesystem::filesystem_error &exception) {
    std::cerr << exception.what() << "\n";
    return 1;
  }

  std::filesystem::path output_filename =
      std::filesystem::absolute(input_filename).parent_path();
  output_filename /= input_filename.stem();
  output_filename += "_" + op_mode + "_";
  output_filename += argv[1];
  output_filename += input_filename.extension();

  std::ifstream input(input_filename, std::ios::in | std::ios::binary);
  std::ofstream output(output_filename, std::ios::out | std::ios::binary);

  if (!copy_header(input, output)) {
    fallback(output, output_filename);
    return 1;
  }

  if (!do_crypt(input, output, cipher, to_encrypt ? AES_ENCRYPT : AES_DECRYPT,
                op_mode)) {
    fallback(output, output_filename);
    return 1;
  }

  return 0;
}
