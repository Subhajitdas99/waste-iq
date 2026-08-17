import {
  MutationCache,
  QueryCache,
  QueryClient,
  type DefaultOptions,
} from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { getApiErrorMessage } from "@/lib/api-error";

const QUERY_STALE_TIME_MS = 60_000;
const QUERY_GC_TIME_MS = 5 * 60_000;

export interface AppQueryMeta extends Record<string, unknown> {
  errorMessage?: string;
  suppressGlobalError?: boolean;
}

export interface QueryErrorPayload {
  source: "query" | "mutation";
  message: string;
  error: unknown;
  key?: readonly unknown[];
}

type QueryErrorHandler = (payload: QueryErrorPayload) => void;

declare module "@tanstack/react-query" {
  interface Register {
    queryMeta: AppQueryMeta;
    mutationMeta: AppQueryMeta;
  }
}

function defaultQueryErrorHandler(payload: QueryErrorPayload) {
  console.error(
    `[Waste-IQ Query ${payload.source} Error] ${payload.message}`,
    {
      key: payload.key,
      error: payload.error,
    },
  );
}

let queryErrorHandler: QueryErrorHandler = defaultQueryErrorHandler;

export function setGlobalQueryErrorHandler(handler: QueryErrorHandler | null) {
  queryErrorHandler = handler ?? defaultQueryErrorHandler;
}

function shouldRetryRequest(failureCount: number, error: unknown) {
  if (isAxiosError(error)) {
    const status = error.response?.status;

    if (status !== undefined) {
      const isRetryableClientError = status === 408 || status === 429;

      if (status >= 400 && status < 500 && !isRetryableClientError) {
        return false;
      }
    }
  }

  return failureCount < 2;
}

function notifyGlobalError(options: {
  error: unknown;
  key?: readonly unknown[];
  meta?: AppQueryMeta;
  source: "query" | "mutation";
}) {
  if (options.meta?.suppressGlobalError) {
    return;
  }

  queryErrorHandler({
    source: options.source,
    key: options.key,
    error: options.error,
    message: getApiErrorMessage(
      options.error,
      options.meta?.errorMessage ?? "We couldn't load this data. Please try again.",
    ),
  });
}

export function createAppQueryClient(
  overrides: DefaultOptions = {},
): QueryClient {
  return new QueryClient({
    queryCache: new QueryCache({
      onError: (error, query) => {
        notifyGlobalError({
          error,
          key: query.queryKey,
          meta: query.meta,
          source: "query",
        });
      },
    }),
    mutationCache: new MutationCache({
      onError: (error, _variables, _context, mutation) => {
        notifyGlobalError({
          error,
          key: mutation.options.mutationKey,
          meta: mutation.meta,
          source: "mutation",
        });
      },
    }),
    defaultOptions: {
      queries: {
        retry: shouldRetryRequest,
        staleTime: QUERY_STALE_TIME_MS,
        gcTime: QUERY_GC_TIME_MS,
        refetchOnWindowFocus: false,
        ...overrides.queries,
      },
      mutations: {
        retry: false,
        ...overrides.mutations,
      },
    },
  });
}

export const queryClient = createAppQueryClient();
