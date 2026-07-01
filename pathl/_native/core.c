#define PY_SSIZE_T_CLEAN
#include <Python.h>

/* Przykładowa funkcja natywna: szybkie liczenie długości ścieżki */
static PyObject *
core_path_depth(PyObject *self, PyObject *args)
{
    const char *path;
    if (!PyArg_ParseTuple(args, "s", &path)) {
        return NULL;
    }

    int depth = 0;
    for (const char *p = path; *p; p++) {
        if (*p == '/' || *p == '\\') {
            depth++;
        }
    }

    return PyLong_FromLong(depth);
}

static PyMethodDef CoreMethods[] = {
    {"path_depth", core_path_depth, METH_VARARGS,
     "Zwraca głębokość ścieżki (liczbę separatorów)."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef coremodule = {
    PyModuleDef_HEAD_INIT,
    "core",
    "Natywny moduł pathl (C extension)",
    -1,
    CoreMethods
};

PyMODINIT_FUNC
PyInit_core(void)
{
    return PyModule_Create(&coremodule);
}