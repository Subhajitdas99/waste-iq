import { useMutation, useQueryClient } from "@tanstack/react-query";
import { register as registerRequest } from "@/api/auth";
import { useAuth } from "@/context/AuthContext";
import { authQueryKeys } from "@/hooks/auth-query-keys";
import type { RegisterPayload } from "@/types/auth";

export interface RegisterMutationVariables extends RegisterPayload {
  autoLogin?: boolean;
  rememberMe?: boolean;
}

export function useRegister() {
  const queryClient = useQueryClient();
  const { login } = useAuth();

  return useMutation({
    meta: { suppressGlobalError: true },
    mutationFn: ({ autoLogin: _autoLogin, rememberMe: _rememberMe, ...payload }: RegisterMutationVariables) =>
      registerRequest(payload),
    onSuccess: (response, variables) => {
      if (!variables.autoLogin) {
        return;
      }

      login(
        response.access_token,
        response.user,
        variables.rememberMe,
        response.refresh_token,
      );
      queryClient.setQueryData(authQueryKeys.currentUser, response.user);
    },
  });
}
