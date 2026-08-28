#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>     // close function prototype
#include <arpa/inet.h>  // sockaddr_in struct prototype

#define PORT 12000
#define BUFFER_SIZE 1024    // buffer size for message and response

int main() {

    int server_fd;      // server socket descriptor 
    int client_fd;      // client socket descriptor

    struct sockaddr_in server_addr;
    struct sockaddr_in client_addr;

    socklen_t client_len = sizeof(client_addr);

    char buffer[BUFFER_SIZE];

    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    if (server_fd < 0) {
        perror("socket");
        return 1;
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(
        server_fd,
        (struct sockaddr *)&server_addr,
        sizeof(server_addr)
    ) < 0) {

        perror("bind");
        close(server_fd);
        return 1;
    }

    listen(server_fd, 10);

    printf("C server ready on port %d\n", PORT);

    while (1) {

        client_fd = accept(
            server_fd,
            (struct sockaddr *)&client_addr,
            &client_len
        );

        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        memset(buffer, 0, BUFFER_SIZE);

        int bytes = recv(
            client_fd,
            buffer,
            BUFFER_SIZE - 1,
            0
        );

        if (bytes > 0) {

            printf(
                "Received from %s: %s\n",
                inet_ntoa(client_addr.sin_addr),
                buffer
            );

            for (int i = 0; i < bytes; i++) {
                buffer[i] = toupper(
                    (unsigned char) buffer[i]
                );
            }

            send(client_fd, buffer, bytes, 0);
        }

        close(client_fd);
    }

    close(server_fd);

    return 0;
}