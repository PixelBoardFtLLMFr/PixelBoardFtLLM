#ifndef TRACE_H
#define TRACE_H

#ifndef NDEBUG
#define TRACE printf("trace: %s\n", __func__)
#else
#define TRACE
#endif

#endif
