/* IDF's NDEBUG assert still evaluates expressions, including SQLite debug-only
 * identifiers. Use standard release semantics only in this translation unit. */
#define NDEBUG 1
#include <assert.h>
#undef assert
#define assert(expression) ((void)0)
