import { builtinEnvironments } from "vitest/environments";
import type { Environment } from "vitest/environments";

const jsdomEnvironment = builtinEnvironments.jsdom;

const environment: Environment = {
  name: "jsdom-compat",
  transformMode: "web",
  async setup(global, options) {
    // Capture the Node natives before the jsdom environment populates the
    // global with jsdom's own classes (vitest populateGlobal). jsdom does not
    // implement fetch/Request, so Node's undici versions stay global; undici
    // brand-checks its inputs against Node's own classes, which jsdom's
    // implementations can never satisfy.
    const nativeAbortController = globalThis.AbortController;
    const nativeAbortSignal = globalThis.AbortSignal;
    const nativeFormData = globalThis.FormData;
    const nativeReadableStream = globalThis.ReadableStream;

    const result = await jsdomEnvironment.setup(global, options);

    // --- AbortSignal bridge ---
    // The global AbortController/AbortSignal must stay jsdom's: framer-motion
    // passes `new AbortController().signal` into jsdom's addEventListener
    // options, and jsdom brand-checks signals against its own AbortSignal
    // class. React Router instead feeds its navigation controller's signal
    // into `new Request(...)`, and undici's Request brand-checks signals
    // against Node's native AbortSignal, throwing "Expected signal (...) to be
    // an instance of AbortSignal" for jsdom signals. Since one global cannot
    // satisfy both consumers, keep jsdom's globals and convert jsdom signals
    // to linked native signals at the Request boundary.
    const originalRequest = globalThis.Request;

    const requestProxy = new Proxy(originalRequest, {
      construct(target, args, newTarget) {
        const [input, init] = args;
        const signal = init?.signal;
        if (
          signal != null &&
          !(signal instanceof nativeAbortSignal) &&
          typeof signal.addEventListener === "function"
        ) {
          const bridge = new nativeAbortController();
          signal.addEventListener(
            "abort",
            () => bridge.abort(signal.reason),
            { once: true },
          );
          args = [input, { ...init, signal: bridge.signal }];
        }
        return Reflect.construct(target, args, newTarget);
      },
    });

    Object.defineProperty(globalThis, "Request", {
      configurable: true,
      writable: true,
      value: requestProxy,
    });

    // --- FormData bridge ---
    // undici's Request recognizes FormData bodies via `instanceof` against
    // Node's FormData. jsdom's FormData instances fail that check, so undici
    // stringifies the body (Content-Type becomes text/plain) and
    // `request.formData()` in msw handlers throws. Bridge jsdom's FormData
    // into Node's prototype chain so both realms accept the same instances.
    Object.setPrototypeOf(global.FormData.prototype, nativeFormData.prototype);

    // undici's multipart encoder reads File/Blob values through
    // Blob.prototype.stream(), which jsdom 29 does not implement. Polyfill it
    // (backed by Node's ReadableStream and jsdom's own arrayBuffer()) so
    // binary parts survive the encoding.
    if (typeof global.Blob.prototype.stream !== "function") {
      Object.defineProperty(global.Blob.prototype, "stream", {
        configurable: true,
        writable: true,
        value: function stream(): ReadableStream<Uint8Array> {
          const readBuffer = Blob.prototype.arrayBuffer.bind(this);
          let started = false;
          return new nativeReadableStream({
            async pull(controller) {
              if (started) {
                controller.close();
                return;
              }
              started = true;
              controller.enqueue(new Uint8Array(await readBuffer()));
              controller.close();
            },
          });
        },
      });
    }

    return {
      ...result,
      teardown(global) {
        if (globalThis.Request === requestProxy) {
          Object.defineProperty(globalThis, "Request", {
            configurable: true,
            writable: true,
            value: originalRequest,
          });
        }
        return result.teardown(global);
      },
    };
  },
};

export default environment;
