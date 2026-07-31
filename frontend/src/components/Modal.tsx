import * as Dialog from "@radix-ui/react-dialog";
import type { ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "./ui/button";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
}: ModalProps) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-card shadow-xl">
          <div className="flex flex-col p-6 space-y-1.5 text-center sm:text-left border-b">
            <Dialog.Title className="text-lg font-semibold leading-none tracking-tight">
              {title}
            </Dialog.Title>
            {description ? (
              <Dialog.Description className="text-sm text-muted-foreground">
                {description}
              </Dialog.Description>
            ) : null}
            <Dialog.Close
              aria-label="Close dialog"
              className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>
          <div className="p-6">{children}</div>
          <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 p-6 pt-0 border-t mt-4">
            {footer ?? (
              <Dialog.Close asChild>
                <Button variant="outline">Close</Button>
              </Dialog.Close>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
