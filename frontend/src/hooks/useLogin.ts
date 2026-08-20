import { useMutation, useQueryClient } from "@tanstack/react-query";
import { login as loginRequest } from "@/api/auth";
import { useAuth } from "@/context/AuthContext";
import { authQueryKeys } from "@/hooks/auth-query-keys";
import type { LoginPayload } from "@/types/auth";

export interface LoginMutationVariables extends LoginPayload {
  rememberMe?: boolean;
}

interface LoginMutationResult {
  access_token: string;
  refresh_token: string;
  user: Awaited<ReturnType<typeof loginRequest>>["user"];
  rememberMe: boolean;
}

export function useLogin() {
  const queryClient = useQueryClient();
  const { login } = useAuth();

  return useMutation({
    meta: {
      suppressGlobalError: true,
    },
    mutationFn: async ({
      rememberMe = true,
      ...credentials
    }: LoginMutationVariables): Promise<LoginMutationResult> => {
      const response = await loginRequest(credentials);

      return {
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        user: response.user,
        rememberMe,
      };
    },
    onSuccess: ({ access_token, refresh_token, user, rememberMe }) => {
      login(access_token, user, rememberMe, refresh_token);
      queryClient.setQueryData(authQueryKeys.currentUser, user);
    },
  });
}
