#include <stdio.h>
#include <stdlib.h> // free function prototype
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include <arpa/inet.h>  //socket, IPv4 address, conversiones de direcciones IP
#include <pthread.h>    //multithreading library

#define BUFFER_SIZE 1024    // buffer size for message and response


void *handle_client(void *arg)  // esta función es llamada por el hilo principal
{
    int clientSocket = *((int *) arg); // se recupera el socket del cliente

    free(arg);  // se libera la memoria asignada al socket

    char buffer[BUFFER_SIZE];   // buffer para el mensaje y la respuesta

    int bytesReceived = recv(   // se recibe el mensaje del cliente
        clientSocket,            // socket del cliente
        buffer,                  // buffer para el mensaje
        BUFFER_SIZE - 1,         // tamaño del buffer
        0                        // opciones de recepción   
    );

    if (bytesReceived > 0)       // si se recibió un mensaje
    {
        buffer[bytesReceived] = '\0';   // se termina el mensaje con un caracter nulo

        printf(
            "[THREAD] Received: %s\n",
            buffer
        );

        for (int i = 0; i < bytesReceived; i++)  // se convierte a mayúsculas cada caracter del mensaje
        {
            buffer[i] = toupper(            // se convierte a mayúsculas cada caracter del mensaje
                (unsigned char) buffer[i]   // se convierte a mayúsculas cada caracter del mensaje
            );
        }

        sleep(3);

        send(                              // se envía el mensaje al cliente
            clientSocket,                  // socket del cliente
            buffer,                        // mensaje a enviar
            bytesReceived,                 // tamaño del mensaje
            0                              // opciones de envío
        );

        printf(
            "[THREAD] Response sent\n"
        );
    }

    close(clientSocket);    // se cierra el socket del cliente

    printf(
        "[THREAD] Connection closed\n"
    );

    return NULL;
}


int main(int argc, char *argv[])    // se ejecuta el programa
{
    int port = 22000;

    if (argc >= 2)
    {
        port = atoi(argv[1]);
    }

    int serverSocket = socket(
        AF_INET,
        SOCK_STREAM,
        0
    );

    if (serverSocket < 0)
    {
        perror("socket");
        return 1;
    }

    int option = 1;

    setsockopt(
        serverSocket,
        SOL_SOCKET,
        SO_REUSEADDR,
        &option,
        sizeof(option)
    );

    struct sockaddr_in serverAddress;

    memset(
        &serverAddress,
        0,
        sizeof(serverAddress)
    );

    serverAddress.sin_family = AF_INET;
    serverAddress.sin_addr.s_addr = INADDR_ANY;
    serverAddress.sin_port = htons(port);

    if (
        bind(
            serverSocket,
            (struct sockaddr *) &serverAddress,
            sizeof(serverAddress)
        ) < 0
    )
    {
        perror("bind");
        close(serverSocket);
        return 1;
    }

    if (listen(serverSocket, 10) < 0)
    {
        perror("listen");
        close(serverSocket);
        return 1;
    }

    printf(
        "C threaded server ready on port %d\n",
        port
    );

    while (1)
    {
        struct sockaddr_in clientAddress;
        socklen_t clientLength =
            sizeof(clientAddress);

        int *clientSocket =
            malloc(sizeof(int));

        *clientSocket = accept(
            serverSocket,
            (struct sockaddr *) &clientAddress,
            &clientLength
        );

        if (*clientSocket < 0)
        {
            perror("accept");
            free(clientSocket);
            continue;
        }

        printf(
            "Client connected: %s:%d\n",
            inet_ntoa(clientAddress.sin_addr),
            ntohs(clientAddress.sin_port)
        );

        pthread_t thread;

        if (
            pthread_create(
                &thread,
                NULL,
                handle_client,
                clientSocket
            ) != 0
        )
        {
            perror("pthread_create");
            close(*clientSocket);
            free(clientSocket);
            continue;
        }

        pthread_detach(thread);
    }

    close(serverSocket);

    return 0;
}