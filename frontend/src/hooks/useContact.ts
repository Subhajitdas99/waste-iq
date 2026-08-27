import { useMutation } from "@tanstack/react-query";
import { initiateContact } from "@/api/pickupRequests";
import type { ContactSessionRead } from "@/types/pickup";

export function useInitiateContact() {
  return useMutation<ContactSessionRead, Error, number>({
    mutationFn: (requestId: number) => initiateContact(requestId),
  });
}
