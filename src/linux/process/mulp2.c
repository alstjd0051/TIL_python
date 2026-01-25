#include <stdio.h>
#include <unistd.h>

int main() {
    printf("my pid is %d",getpid());
    if(fork() == 0){
        printf("child pid is %d",getpid());
    }
    return 0;
}
