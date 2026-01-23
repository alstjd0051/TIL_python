#include <stdio.h>
#include <unistd.h>

void foo() {
    printf("foo executed! \n");
}

int main() {
    printf("my pid is %d",getpid());
    if(fork() == 0){
        printf("child pid is %d",getpid());
    }else {
        printf("parent pid is %d",getpid());
        foo();
    }
    printf("executed! \n");
    return 0;
}