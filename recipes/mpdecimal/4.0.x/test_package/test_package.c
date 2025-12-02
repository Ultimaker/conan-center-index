#include <mpdecimal.h>
#include <stdio.h>

int main(void) {
    mpd_context_t ctx;
    mpd_t *a, *b, *result;
    char *rstring;

    mpd_defaultcontext(&ctx);

    a = mpd_new(&ctx);
    b = mpd_new(&ctx);
    result = mpd_new(&ctx);

    mpd_set_string(a, "1.234", &ctx);
    mpd_set_string(b, "2.345", &ctx);

    mpd_add(result, a, b, &ctx);

    rstring = mpd_to_sci(result, 1);
    printf("Result: %s\n", rstring);

    mpd_del(a);
    mpd_del(b);
    mpd_del(result);
    mpd_free(rstring);

    return 0;
}
