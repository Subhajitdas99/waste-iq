import { InputHTMLAttributes } from "react";
import { UseFormRegisterReturn, FieldError } from "react-hook-form";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { cn } from "@/lib/utils";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  registration: Partial<UseFormRegisterReturn>;
  error?: FieldError;
}

export function FormField({ label, registration, error, className, id, ...props }: FormFieldProps) {
  const fieldId = id || registration.name;
  return (
    <div className={cn("flex flex-col space-y-2 mb-4", className)}>
      <Label htmlFor={fieldId} className={error ? "text-destructive" : ""}>
        {label}
      </Label>
      <Input
        id={fieldId}
        className={error ? "border-destructive focus-visible:ring-destructive" : ""}
        {...registration}
        {...props}
      />
      {error?.message && (
        <span className="text-sm font-medium text-destructive">
          {error.message}
        </span>
      )}
    </div>
  );
}
