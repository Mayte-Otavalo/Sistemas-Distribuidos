#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 12000
#define BUFFER_SIZE 1024

int main(int argc, char *argv[]) {

    int sock;

    struct sockaddr_in server_addr;

    char message[BUFFER_SIZE];
    char response[BUFFER_SIZE];

    char *server_ip = "127.0.0.1";

    if (argc > 1) {
        server_ip = argv[1];
    }

    sock = socket(AF_INET, SOCK_STREAM, 0);

    if (sock < 0) {
        perror("socket");
        return 1;
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);

    if (
        inet_pton(
            AF_INET,
            server_ip,
            &server_addr.sin_addr
        ) <= 0
    ) {

        printf("Invalid IP\n");
        close(sock);
        return 1;
    }

    if (
        connect(
            sock,
            (struct sockaddr *)&server_addr,
            sizeof(server_addr)
        ) < 0
    ) {

        perror("connect");
        close(sock);
        return 1;
    }

    printf("Enter message: ");

    fgets(
        message,
        BUFFER_SIZE,
        stdin
    );

    message[strcspn(message, "\n")] = 0;

    send(
        sock,
        message,
        strlen(message),
        0
    );

    memset(response, 0, BUFFER_SIZE);

    recv(
        sock,
        response,
        BUFFER_SIZE - 1,
        0
    );

    printf(
        "From server: %s\n",
        response
    );

    close(sock);

    return 0;
}