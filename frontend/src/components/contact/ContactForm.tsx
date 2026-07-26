import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Toast } from "@/components/Toast";

const contactSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  subject: z.string().min(5, "Subject must be at least 5 characters"),
  message: z.string().min(10, "Message must be at least 10 characters"),
});

type ContactFormValues = z.infer<typeof contactSchema>;

export function ContactForm() {
  const [isSubmitted, setIsSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<ContactFormValues>({
    resolver: zodResolver(contactSchema),
  });

  const onSubmit = async (data: ContactFormValues) => {
    await new Promise((resolve) => setTimeout(resolve, 800));
    console.info("Contact form submission (frontend-only):", data);
    setIsSubmitted(true);
    reset();
    setTimeout(() => setIsSubmitted(false), 5000);
  };

  return (
    <>
      {isSubmitted && (
        <Toast
          message="Message sent successfully! We'll get back to you soon."
          type="success"
        />
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField
            label="Full Name"
            placeholder="John Doe"
            registration={register("name")}
            error={errors.name}
          />
          <FormField
            label="Email"
            type="email"
            placeholder="john@example.com"
            registration={register("email")}
            error={errors.email}
          />
        </div>

        <FormField
          label="Subject"
          placeholder="How can we help you?"
          registration={register("subject")}
          error={errors.subject}
        />

        <div className="flex flex-col space-y-2 mb-4">
          <label
            htmlFor="message"
            className={`text-sm font-medium leading-none ${errors.message ? "text-destructive" : ""}`}
          >
            Message
          </label>
          <textarea
            id="message"
            className={`flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y ${errors.message ? "border-destructive focus-visible:ring-destructive" : ""}`}
            placeholder="Tell us a little more about your inquiry..."
            {...register("message")}
          />
          {errors.message && (
            <span className="text-sm font-medium text-destructive">
              {errors.message.message}
            </span>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? (
            "Sending..."
          ) : (
            <>
              Send Message <Send className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>
    </>
  );
}
