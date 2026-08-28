#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>

#define BUFFER_SIZE 1024


typedef struct
{
    int client_id;
    char server_ip[50];
    int port;
}
ClientArguments;


void generate_message(
    char *message,
    int length,
    unsigned int *seed
)
{
    const char letters[] =
        "abcdefghijklmnopqrstuvwxyz";

    for (int i = 0; i < length; i++)
    {
        message[i] =
            letters[
                rand_r(seed) % 26
            ];
    }

    message[length] = '\0';
}


void *client_task(void *arg)
{
    ClientArguments *data =
        (ClientArguments *) arg;

    unsigned int seed =
        time(NULL)
        ^
        data->client_id
        ^
        (unsigned int) pthread_self();

    int numberMessages =
        2 + rand_r(&seed) % 4;

    printf(
        "[CLIENT %d] Will send %d messages\n",
        data->client_id,
        numberMessages
    );


    for (int i = 0; i < numberMessages; i++)
    {
        int clientSocket = socket(
            AF_INET,
            SOCK_STREAM,
            0
        );

        if (clientSocket < 0)
        {
            perror("socket");
            continue;
        }

        struct sockaddr_in serverAddress;

        memset(
            &serverAddress,
            0,
            sizeof(serverAddress)
        );

        serverAddress.sin_family = AF_INET;
        serverAddress.sin_port =
            htons(data->port);

        if (
            inet_pton(
                AF_INET,
                data->server_ip,
                &serverAddress.sin_addr
            ) <= 0
        )
        {
            printf("Invalid IP address\n");

            close(clientSocket);

            break;
        }


        if (
            connect(
                clientSocket,
                (struct sockaddr *) &serverAddress,
                sizeof(serverAddress)
            ) < 0
        )
        {
            perror("connect");

            close(clientSocket);

            continue;
        }


        char message[50];

        int length =
            5 + rand_r(&seed) % 11;

        generate_message(
            message,
            length,
            &seed
        );


        printf(
            "[CLIENT %d] Message %d: %s\n",
            data->client_id,
            i + 1,
            message
        );


        send(
            clientSocket,
            message,
            strlen(message),
            0
        );


        char response[BUFFER_SIZE];

        int bytesReceived = recv(
            clientSocket,
            response,
            BUFFER_SIZE - 1,
            0
        );


        if (bytesReceived > 0)
        {
            response[bytesReceived] = '\0';

            printf(
                "[CLIENT %d] Response: %s\n",
                data->client_id,
                response
            );
        }


        close(clientSocket);

        usleep(300000);
    }


    printf(
        "[CLIENT %d] Finished\n",
        data->client_id
    );

    return NULL;
}


int main(int argc, char *argv[])
{
    if (argc < 4)
    {
        printf(
            "Usage: %s <server_ip> "
            "<port> <number_clients>\n",
            argv[0]
        );

        printf(
            "Example: %s 127.0.0.1 22000 3\n",
            argv[0]
        );

        return 1;
    }


    int port = atoi(argv[2]);

    int numberClients = atoi(argv[3]);


    pthread_t threads[numberClients];

    ClientArguments arguments[numberClients];


    for (int i = 0; i < numberClients; i++)
    {
        arguments[i].client_id = i + 1;

        strcpy(
            arguments[i].server_ip,
            argv[1]
        );

        arguments[i].port = port;


        pthread_create(
            &threads[i],
            NULL,
            client_task,
            &arguments[i]
        );
    }


    for (int i = 0; i < numberClients; i++)
    {
        pthread_join(
            threads[i],
            NULL
        );
    }


    printf(
        "All C clients finished.\n"
    );


    return 0;
}