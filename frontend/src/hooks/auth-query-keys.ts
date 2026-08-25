export const authQueryKeys = {
  all: ["auth"] as const,
  currentUser: ["auth", "current-user"] as const,
  loginHistory: (page = 1, pageSize = 10) =>
    ["auth", "login-history", { page, pageSize }] as const,
};
