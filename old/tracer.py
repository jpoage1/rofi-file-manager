# Path: old/tracer.py
# Last Modified: 2025-06-11

# tracer.py
import io
import sys

class OutputTracer:
    def __enter__(self):
        self._stdout = sys.stdout
        self._buffer = io.StringIO()
        sys.stdout = self._buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._stdout
        self.output = self._buffer.getvalue()
        self._buffer.close()

# Usage:
with OutputTracer() as tracer:
    print("trace start")
    # ... code you want to trace
    print("trace end")

print("Captured output:")
print(tracer.output)
