#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <openssl/ssl.h>
#include <sys/socket.h>
#include <unistd.h>

#define BOLD_RED "\033[1m\033[31m"
#define NORMAL_COLOR "\033[0m"

#ifndef ENABLE_COLORS
#define ENABLE_COLORS 1
#endif

#if ENABLE_COLORS
#define ERROR(fmt, ...)                                                        \
  fprintf(stderr, BOLD_RED "[error]: " NORMAL_COLOR fmt, __VA_ARGS__);
#else
#define ERROR(fmt, ...) fprintf(stderr, "[error]: " fmt, __VA_ARGS__);
#endif

#define BUFFER_SIZE 4096

#define IPv4_ADDR "147.32.232.212" // IPv6_ADDR 2001:718:2:2908::212
#define HTTPS_PORT 443
#define FIT_CTU_HOST "fit.cvut.cz"
#define FIT_CTU_URL "/cs/fakulta/o-fakulte"
#define GET_REQUEST                                                            \
  "GET " FIT_CTU_URL " HTTP/1.1\r\nHost: " FIT_CTU_HOST                        \
  "\r\nConnection: close\r\n\r\n"

bool close_resources(SSL *ssl, SSL_CTX *ctx, int socket_fd,
                     FILE *certificate_file_ptr, FILE *webpagesource_file_ptr,
                     const char *const certificate_filename,
                     const char *const webpagesource_filename,
                     bool delete_files) {

  bool success = true;

  if (ssl != NULL) {
    int shutdown = SSL_shutdown(ssl);

    if (shutdown == 0) {
      // have no idea, what's wrong. Should return 1.
    } else if (shutdown < 0) {
      ERROR("%s", "SSL_shutdown() failed\n");
      ERROR("SSL_get_error() == %d\n", SSL_get_error(ssl, shutdown));
      success = false;
    }
  }

  if (close(socket_fd) != 0) {
    ERROR("cannot close %d socket\n", socket_fd);
    success = false;
  }

  SSL_free(ssl);
  SSL_CTX_free(ctx);

  if (fclose(webpagesource_file_ptr) != 0) {
    ERROR("cannot close %s\n", webpagesource_filename);
    success = false;
  }

  if (fclose(certificate_file_ptr) != 0) {
    ERROR("cannot close %s\n", certificate_filename);
    success = false;
  }

  if (delete_files) {
    if (remove(certificate_filename) != 0) {
      ERROR("cannot remove %s\n", certificate_filename);
      success = false;
    } else {
      printf("Removed: %s\n", certificate_filename);
    }

    if (remove(webpagesource_filename) != 0) {
      ERROR("cannot remove %s\n", webpagesource_filename);
      success = false;
    } else {
      printf("Removed: %s\n", webpagesource_filename);
    }
  }

  return success;
}

bool download_webpage_source(SSL *ssl, FILE *webpagesource_file_ptr,
                             const char *const webpagesource_filename) {

  char buffer[BUFFER_SIZE];
  int return_code = 0, received = 0;

  printf(GET_REQUEST);

  if ((return_code = SSL_write(ssl, GET_REQUEST, sizeof(GET_REQUEST))) <= 0) {
    ERROR("cannot send GET request to %s%s", FIT_CTU_HOST, FIT_CTU_URL);
    ERROR("SSL_get_error() == %d\n", SSL_get_error(ssl, return_code));
    return false;
  }

  while (42) {
    received = SSL_read(ssl, buffer, BUFFER_SIZE);

    // EOF
    if (received == 0) {
      break;
    }

    if (received < 0) {
      ERROR("%s", "received < 0 for SSL_read()\n");
      return false;
    }

    if (!fwrite(buffer, sizeof(*buffer), received, webpagesource_file_ptr)) {
      ERROR("cannot write to %s\n", webpagesource_filename);
      return false;
    }
  }

  printf("Saved web page source to %s\n", webpagesource_filename);
  return true;
}

SSL *create_and_setup_ssl_struct(SSL_CTX *ctx, int socket_fd) {

  SSL *ssl = SSL_new(ctx);

  if (!ssl) {
    ERROR("%s", "SSL_new() failed\n");
    return NULL;
  }

  if (!SSL_set_fd(ssl, socket_fd)) {
    ERROR("SSL_set_fd() failed. Cannot set socket (%d) to ssl struct\n",
          socket_fd);
    return NULL;
  }

  if (!SSL_set_tlsext_host_name(ssl, FIT_CTU_HOST)) {
    ERROR("SSL_set_tlsext_host_name() failed for %s\n", FIT_CTU_HOST);
    return NULL;
  }

  return ssl;
}

bool create_socket_and_connect(int *socket_fd, struct sockaddr_in *servaddr) {

  *socket_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

  if (*socket_fd == -1) {
    ERROR("%s", "socket() failed\n");
    return false;
  }

  if (connect(*socket_fd, (struct sockaddr *)servaddr, sizeof(*servaddr)) ==
      -1) {
    ERROR("cannot connect to %s:%d\n", IPv4_ADDR, HTTPS_PORT);
    return false;
  }

  return true;
}

int main(int argc, char *argv[]) {
  if (argc != 3) {
    fprintf(stderr,
            "%s FILECERT FILEPAGE\n\n"
            "FILECERT   = arg       filepath to save certificate to\n"
            "FILEPAGE   = arg       filepath to save webpage source to\n",
            argv[0]);
    return 1;
  }

  const char *const certificate_filename = argv[1];
  const char *const webpagesource_filename = argv[2];

  FILE *certificate_file_ptr = fopen(certificate_filename, "w");
  if (!certificate_file_ptr) {
    ERROR("cannot open output file \"%s\" for writing\n", certificate_filename);
    return 1;
  }

  FILE *webpagesource_file_ptr = fopen(webpagesource_filename, "w");
  if (!webpagesource_file_ptr) {
    ERROR("cannot open output file \"%s\" for writing\n",
          webpagesource_filename);

    fclose(certificate_file_ptr);
    return 1;
  }

  struct sockaddr_in servaddr;
  memset(&servaddr, 0, sizeof(servaddr));
  servaddr.sin_family = AF_INET;
  servaddr.sin_addr.s_addr = inet_addr(IPv4_ADDR);
  servaddr.sin_port = htons(HTTPS_PORT);

  int socket_fd;

  if (!create_socket_and_connect(&socket_fd, &servaddr)) {
    close_resources(NULL, NULL, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  SSL_library_init();
  SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());

  if (!ctx) {
    ERROR("%s", "SSL_CTX_new() failed\n");
    close_resources(NULL, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  SSL_CTX_set_options(ctx, SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 | SSL_OP_NO_TLSv1 |
                               SSL_OP_NO_TLSv1_1);

  if (!SSL_CTX_set_default_verify_paths(ctx)) {
    ERROR("%s", "SSL_CTX_set_default_verify_paths() failed\n");
    close_resources(NULL, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  SSL *ssl = create_and_setup_ssl_struct(ctx, socket_fd);

  if (!ssl) {
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  int return_code = 0;

  if ((return_code = SSL_connect(ssl)) != 1) {
    ERROR("SSL_connect() failed. SSL_get_error() == %d\n",
          SSL_get_error(ssl, return_code));

    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  const char *const used_cipher = SSL_get_cipher_name(ssl);
  printf("Server and client agreed to use cipher: %s.\n", used_cipher);

  puts("Simulating cipher vulnerability and preventing usage of this cipher.");
  printf("Disabling: %s\n", used_cipher);

  // Drop old ssl struct, close the socket.
  // Make new socket, reconnect, make new ssl struct.
  SSL_free(ssl);
  close(socket_fd);

  if (!create_socket_and_connect(&socket_fd, &servaddr)) {
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  ssl = create_and_setup_ssl_struct(ctx, socket_fd);
  if (!ssl) {
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  // from `man SSL_set_ciphersuites`
  char *allowed_ciphers[] = {
      "TLS_AES_128_GCM_SHA256", "TLS_CHACHA20_POLY1305_SHA256",
      "TLS_AES_128_CCM_SHA256", "TLS_AES_128_CCM_8_SHA256",
      "TLS_AES_256_GCM_SHA384"};

  int allowed_ciphers_length =
      sizeof(allowed_ciphers) / sizeof(allowed_ciphers[0]);

  char new_allowed_ciphers[1000];
  int new_allowed_ciphers_pointer = 0;

  // iterate through allowed_ciphers, add ciphers which are different from used
  // to the list
  for (int i = 0; i < allowed_ciphers_length; i++) {
    int cipher_len = strlen(allowed_ciphers[i]);

    if (strncmp(used_cipher, allowed_ciphers[i], cipher_len) != 0) {
      strcpy(new_allowed_ciphers + new_allowed_ciphers_pointer,
             allowed_ciphers[i]);
      new_allowed_ciphers_pointer += cipher_len;
    }

    if (i < allowed_ciphers_length - 2) {
      strcpy(new_allowed_ciphers + new_allowed_ciphers_pointer, ":");
      new_allowed_ciphers_pointer++;
    }
  }

  printf("Passing cipherlist to SSL_set_ciphersuites(): %s\n",
         new_allowed_ciphers);

  if (!SSL_set_ciphersuites(ssl, new_allowed_ciphers)) {
    ERROR("%s", "SSL_set_ciphersuites() failed\n");
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  if ((return_code = SSL_connect(ssl)) != 1) {
    ERROR("SSL_connect() failed. SSL_get_error() == %d\n",
          SSL_get_error(ssl, return_code));

    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  printf("Server and client agreed to use new cipher: %s\n",
         SSL_get_cipher_name(ssl));

  if (SSL_get_verify_result(ssl) != X509_V_OK) {
    ERROR("%s", "SSL_get_verify_result() != X509_V_OK. Verification failed\n");
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  puts("Successfully verified server certificate.");

  if (!download_webpage_source(ssl, webpagesource_file_ptr,
                               webpagesource_filename)) {
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  X509 *certificate = SSL_get_peer_certificate(ssl);
  if (!certificate) {
    ERROR("%s", "SSL_get_peer_certificate() failed. Cannot get certificate\n");
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }

  printf("X509 certificate details:\n");
  X509_NAME_print_ex_fp(stdout, X509_get_subject_name(certificate), 4,
                        XN_FLAG_ONELINE & ~ASN1_STRFLGS_ESC_MSB);
  printf("\n");

  if (!PEM_write_X509(certificate_file_ptr, certificate)) {
    ERROR("PEM_write_X509() failed. Cannot write x509 certificate to %s",
          certificate_filename);
    X509_free(certificate);
    close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                    webpagesource_file_ptr, certificate_filename,
                    webpagesource_filename, true);
    return 1;
  }
  printf("Saved website certificate to %s\n", certificate_filename);

  X509_free(certificate);
  if (!close_resources(ssl, ctx, socket_fd, certificate_file_ptr,
                       webpagesource_file_ptr, certificate_filename,
                       webpagesource_filename, false)) {
    return 1;
  }

  return 0;
}
