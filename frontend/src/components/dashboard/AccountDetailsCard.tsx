import { ProfileCard } from "@/components/dashboard/ProfileCard";
import { formatDateTime } from "@/lib/pickup";
import type { UserProfile } from "@/types/auth";

interface AccountDetailsCardProps {
  user: UserProfile | null | undefined;
}

export function AccountDetailsCard({ user }: AccountDetailsCardProps) {
  return (
    <ProfileCard
      title="Account Details"
      description="Current user attributes loaded from the authentication API."
      items={[
        { label: "Full Name", value: user?.name ?? "Not available" },
        { label: "Email", value: user?.email ?? "Not available" },
        { label: "Phone", value: user?.phone ?? "Not available" },
        { label: "Role", value: user?.role ?? "Not available" },
        { label: "Member Since", value: formatDateTime(user?.created_at) },
        { label: "User ID", value: user ? String(user.id) : "Not available" },
      ]}
    />
  );
}
